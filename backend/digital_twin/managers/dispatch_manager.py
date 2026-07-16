"""DispatchManager: assigns drivers and vehicles to pending trips.

DispatchManager coordinates DriverManager, VehicleManager, and
TripManager to perform assignment. It contains only assignment
*policy* (currently: first-available match); it does not own any
registry itself -- registries are owned by the respective managers.
Sprint 1 uses a simple first-available strategy; the future
`decision/` module is expected to replace this with smarter policies
without changing DispatchManager's public interface.
"""

from __future__ import annotations

import logging

from digital_twin.common.enums import ExecutionPhase
from digital_twin.common.exceptions import AssignmentError, EntityNotFoundError
from digital_twin.managers.driver_manager import DriverManager
from digital_twin.managers.trip_manager import TripManager
from digital_twin.managers.vehicle_manager import VehicleManager
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class DispatchManager:
    """Assigns available drivers and vehicles to pending trips.

    Depends on DriverManager, VehicleManager, and TripManager for
    availability checks and assignment mutation, rather than owning
    any registry of its own.
    """

    def __init__(
        self,
        driver_manager: DriverManager,
        vehicle_manager: VehicleManager,
        trip_manager: TripManager,
    ) -> None:
        """Initialize the dispatch manager.

        Args:
            driver_manager: Source of driver availability/assignment.
            vehicle_manager: Source of vehicle availability/assignment.
            trip_manager: Source of pending trips and assignment.
        """
        self._driver_manager = driver_manager
        self._vehicle_manager = vehicle_manager
        self._trip_manager = trip_manager

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: DispatchManager runs during the DISPATCH phase."""
        return ExecutionPhase.DISPATCH

    def can_dispatch(self, trip_id: str) -> bool:
        """Check whether a trip can currently be dispatched.

        Args:
            trip_id: Id of the trip to check.

        Returns:
            True if there is at least one available driver and one
            available vehicle.

        Raises:
            EntityNotFoundError: If trip_id does not exist.
        """
        self._trip_manager.get_trip(trip_id)
        return bool(
            self._driver_manager.list_available_drivers()
            and self._vehicle_manager.list_available_vehicles()
        )

    def dispatch_trip(self, trip_id: str) -> tuple[str, str]:
        """Assign the first available driver and vehicle to a trip.

        Args:
            trip_id: Id of the pending trip to dispatch.

        Returns:
            A tuple of (driver_id, vehicle_id) that were assigned.

        Raises:
            EntityNotFoundError: If trip_id does not exist.
            AssignmentError: If no driver or no vehicle is available.
        """
        self._trip_manager.get_trip(trip_id)

        available_drivers = self._driver_manager.list_available_drivers()
        if not available_drivers:
            raise AssignmentError(f"No available driver to dispatch trip '{trip_id}'.")

        available_vehicles = self._vehicle_manager.list_available_vehicles()
        if not available_vehicles:
            raise AssignmentError(f"No available vehicle to dispatch trip '{trip_id}'.")

        driver = available_drivers[0]
        vehicle = available_vehicles[0]

        self._driver_manager.assign(driver.driver_id, vehicle.vehicle_id, trip_id)
        self._vehicle_manager.assign(vehicle.vehicle_id, driver.driver_id, trip_id)
        self._trip_manager.assign_trip(trip_id, driver.driver_id, vehicle.vehicle_id)

        logger.info(
            "Dispatched trip %s -> driver=%s vehicle=%s",
            trip_id,
            driver.driver_id,
            vehicle.vehicle_id,
        )
        return driver.driver_id, vehicle.vehicle_id

    def release_assignment(self, driver_id: str, vehicle_id: str) -> None:
        """Release a driver and vehicle back to AVAILABLE.

        Typically called once a trip completes.

        Args:
            driver_id: Id of the driver to release.
            vehicle_id: Id of the vehicle to release.

        Raises:
            EntityNotFoundError: If either id is not registered.
        """
        self._driver_manager.release(driver_id)
        self._vehicle_manager.release(vehicle_id)
        logger.info("Released assignment driver=%s vehicle=%s", driver_id, vehicle_id)

    def on_tick(self, context: TickContext) -> None:
        """Attempt to dispatch every pending trip using first-available policy.

        Args:
            context: The current tick's immutable context.
        """
        for trip in self._trip_manager.list_pending_trips():
            try:
                if self.can_dispatch(trip.trip_id):
                    self.dispatch_trip(trip.trip_id)
            except (AssignmentError, EntityNotFoundError) as exc:
                logger.debug("Dispatch skipped for trip %s: %s", trip.trip_id, exc)