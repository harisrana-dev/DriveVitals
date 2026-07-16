"""FleetManager: fleet-level coordination across drivers, vehicles, trips, shifts.

Per the Digital Twin philosophy, the simulation unit is the *Fleet*,
not an individual vehicle. FleetManager is the composition point that
exposes fleet-wide registries and fleet-level onboarding operations; it
delegates all entity-specific bookkeeping to DriverManager,
VehicleManager, and TripManager rather than duplicating their state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from digital_twin.common.exceptions import (
    ConfigurationError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from digital_twin.config.simulation_config import FleetManagerConfig
from digital_twin.managers.driver_manager import DriverManager, DriverRecord
from digital_twin.managers.trip_manager import TripManager, TripRecord
from digital_twin.managers.vehicle_manager import VehicleManager, VehicleRecord

logger = logging.getLogger(__name__)


@dataclass
class ShiftRecord:
    """Minimal, persistent registry record for a driver's shift.

    Attributes:
        shift_id: Unique identifier for the shift.
        driver_id: Id of the driver this shift belongs to.
        start_time: Simulated time the shift starts.
        end_time: Simulated time the shift is scheduled to end.
    """

    shift_id: str
    driver_id: str
    start_time: datetime
    end_time: datetime


class FleetManager:
    """Owns fleet-level registries by composing the specialized managers.

    FleetManager does not implement its own storage for drivers,
    vehicles, or trips -- it holds references to DriverManager,
    VehicleManager, and TripManager (each the single source of truth
    for its domain) and additionally owns the Shift registry, which has
    no dedicated manager in Sprint 1's module list.

    Note:
        FleetManager is a coordination facade, not a TickableManager --
        it is not registered with the Scheduler. The Scheduler drives
        DriverManager, VehicleManager, TripManager, DispatchManager,
        MaintenanceManager, and EnvironmentManager directly, each in
        its own fixed phase.
    """

    def __init__(
        self,
        config: FleetManagerConfig,
        driver_manager: DriverManager,
        vehicle_manager: VehicleManager,
        trip_manager: TripManager,
    ) -> None:
        """Initialize the fleet manager.

        Args:
            config: Fleet-level capacity configuration.
            driver_manager: The fleet's driver registry.
            vehicle_manager: The fleet's vehicle registry.
            trip_manager: The fleet's trip registry.
        """
        self._config = config
        self._driver_manager = driver_manager
        self._vehicle_manager = vehicle_manager
        self._trip_manager = trip_manager
        self._shifts: dict[str, ShiftRecord] = {}

    @property
    def driver_manager(self) -> DriverManager:
        """DriverManager: The fleet's driver registry."""
        return self._driver_manager

    @property
    def vehicle_manager(self) -> VehicleManager:
        """VehicleManager: The fleet's vehicle registry."""
        return self._vehicle_manager

    @property
    def trip_manager(self) -> TripManager:
        """TripManager: The fleet's trip registry."""
        return self._trip_manager

    def onboard_vehicle(self, vehicle_id: str, vehicle_type: str) -> VehicleRecord:
        """Onboard a new vehicle into the fleet, enforcing capacity limits.

        Args:
            vehicle_id: Unique id for the new vehicle.
            vehicle_type: Vehicle type/class label.

        Returns:
            The newly created VehicleRecord.

        Raises:
            ConfigurationError: If the fleet is already at max capacity.
            EntityAlreadyExistsError: If vehicle_id is already registered.
        """
        if len(self._vehicle_manager.list_vehicles()) >= self._config.max_vehicles:
            raise ConfigurationError(
                f"Fleet vehicle capacity ({self._config.max_vehicles}) reached."
            )
        return self._vehicle_manager.register_vehicle(vehicle_id, vehicle_type)

    def onboard_driver(self, driver_id: str, name: str) -> DriverRecord:
        """Onboard a new driver into the fleet, enforcing capacity limits.

        Args:
            driver_id: Unique id for the new driver.
            name: Display name of the driver.

        Returns:
            The newly created DriverRecord.

        Raises:
            ConfigurationError: If the fleet is already at max capacity.
            EntityAlreadyExistsError: If driver_id is already registered.
        """
        if len(self._driver_manager.list_drivers()) >= self._config.max_drivers:
            raise ConfigurationError(
                f"Fleet driver capacity ({self._config.max_drivers}) reached."
            )
        return self._driver_manager.register_driver(driver_id, name)

    def create_trip(
        self, trip_id: str, origin: str, destination: str, created_at: datetime
    ) -> TripRecord:
        """Create a new trip request for the fleet.

        Args:
            trip_id: Unique id for the new trip.
            origin: Free-form origin label/address.
            destination: Free-form destination label/address.
            created_at: Simulated time of creation.

        Returns:
            The newly created TripRecord.

        Raises:
            EntityAlreadyExistsError: If trip_id already exists.
        """
        return self._trip_manager.create_trip(trip_id, origin, destination, created_at)

    def schedule_shift(
        self, shift_id: str, driver_id: str, start_time: datetime, end_time: datetime
    ) -> ShiftRecord:
        """Schedule a shift for a driver.

        Args:
            shift_id: Unique id for the new shift.
            driver_id: Id of the driver this shift is for.
            start_time: Simulated time the shift starts.
            end_time: Simulated time the shift is scheduled to end.

        Returns:
            The newly created ShiftRecord.

        Raises:
            EntityNotFoundError: If driver_id is not a registered driver.
            EntityAlreadyExistsError: If shift_id already exists.
            ValueError: If end_time is not after start_time.
        """
        # Validate the driver exists; raises EntityNotFoundError otherwise.
        self._driver_manager.get_driver(driver_id)

        if shift_id in self._shifts:
            raise EntityAlreadyExistsError("Shift", shift_id)
        if end_time <= start_time:
            raise ValueError("Shift end_time must be after start_time.")

        record = ShiftRecord(
            shift_id=shift_id,
            driver_id=driver_id,
            start_time=start_time,
            end_time=end_time,
        )
        self._shifts[shift_id] = record
        logger.info("Scheduled shift %s for driver %s", shift_id, driver_id)
        return record

    def get_shift(self, shift_id: str) -> ShiftRecord:
        """Look up a shift by id.

        Args:
            shift_id: Id of the shift to retrieve.

        Returns:
            The matching ShiftRecord.

        Raises:
            EntityNotFoundError: If shift_id is not registered.
        """
        record = self._shifts.get(shift_id)
        if record is None:
            raise EntityNotFoundError("Shift", shift_id)
        return record

    def list_shifts_for_driver(self, driver_id: str) -> list[ShiftRecord]:
        """List all scheduled shifts for a given driver.

        Args:
            driver_id: Id of the driver whose shifts to list.

        Returns:
            All ShiftRecords belonging to driver_id.
        """
        return [s for s in self._shifts.values() if s.driver_id == driver_id]

    def fleet_summary(self) -> dict[str, int]:
        """Produce a fleet-wide snapshot of registry sizes.

        Returns:
            A dict with counts of vehicles, drivers, active trips, and
            scheduled shifts -- useful for dashboards/logging without
            exposing full registry internals.
        """
        return {
            "vehicle_count": len(self._vehicle_manager.list_vehicles()),
            "driver_count": len(self._driver_manager.list_drivers()),
            "active_trip_count": len(self._trip_manager.list_active_trips()),
            "shift_count": len(self._shifts),
        }