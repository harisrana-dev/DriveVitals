"""DispatchManager: assigns drivers and vehicles to pending trips.

DispatchManager coordinates DriverManager, VehicleManager, and
TripManager to perform assignment. It contains only assignment policy
and does not own any registry.

Sprint 1 uses a simple first-available strategy.
"""

from __future__ import annotations

import logging

from digital_twin.common.enums import ExecutionPhase, TripStatus
from digital_twin.common.exceptions import AssignmentError, EntityNotFoundError
from digital_twin.managers.driver_manager import DriverManager
from digital_twin.managers.trip_manager import TripManager
from digital_twin.managers.vehicle_manager import VehicleManager
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class DispatchManager:
    """Assigns available drivers and vehicles to pending trips."""

    def __init__(
        self,
        driver_manager: DriverManager,
        vehicle_manager: VehicleManager,
        trip_manager: TripManager,
    ) -> None:
        """Initialize the dispatch manager."""
        self._driver_manager = driver_manager
        self._vehicle_manager = vehicle_manager
        self._trip_manager = trip_manager

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: DispatchManager runs during DISPATCH."""
        return ExecutionPhase.DISPATCH

    def can_dispatch(self, trip_id: str) -> bool:
        """Check whether a pending trip can currently be dispatched."""
        trip = self._trip_manager.get_trip(trip_id)

        if trip.status != TripStatus.PENDING:
            return False

        return bool(
            self._driver_manager.list_available_drivers()
            and self._vehicle_manager.list_available_vehicles()
        )

    def dispatch_trip(self, trip_id: str) -> tuple[str, str]:
        """Assign the first available driver and vehicle to a pending trip."""
        trip = self._trip_manager.get_trip(trip_id)

        if trip.status != TripStatus.PENDING:
            raise AssignmentError(
                f"Trip '{trip_id}' cannot be dispatched from status "
                f"'{trip.status.value}'."
            )

        available_drivers = self._driver_manager.list_available_drivers()

        if not available_drivers:
            raise AssignmentError(
                f"No available driver to dispatch trip '{trip_id}'."
            )

        available_vehicles = self._vehicle_manager.list_available_vehicles()

        if not available_vehicles:
            raise AssignmentError(
                f"No available vehicle to dispatch trip '{trip_id}'."
            )

        driver = available_drivers[0]
        vehicle = available_vehicles[0]

        driver_id = driver.driver_id
        vehicle_id = vehicle.vehicle_id

        self._driver_manager.assign(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            trip_id=trip_id,
        )

        self._vehicle_manager.assign(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
        )

        self._trip_manager.assign_trip(
            trip_id=trip_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
        )

        logger.info(
            "Dispatched trip %s -> driver=%s vehicle=%s",
            trip_id,
            driver_id,
            vehicle_id,
        )

        return driver_id, vehicle_id

    def release_assignment(
        self,
        driver_id: str,
        vehicle_id: str,
    ) -> None:
        """Release a driver and vehicle back to AVAILABLE."""
        self._driver_manager.release(driver_id)
        self._vehicle_manager.release(vehicle_id)

        logger.info(
            "Released assignment driver=%s vehicle=%s",
            driver_id,
            vehicle_id,
        )

    def on_tick(self, context: TickContext) -> None:
        """Dispatch all pending trips using first-available policy."""
        for trip in self._trip_manager.list_pending_trips():
            try:
                self.dispatch_trip(trip.trip_id)

            except (AssignmentError, EntityNotFoundError) as exc:
                logger.debug(
                    "Dispatch skipped for trip %s: %s",
                    trip.trip_id,
                    exc,
                )