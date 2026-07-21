"""FleetManager: fleet-level coordination across drivers, vehicles, trips, shifts.

Per the Digital Twin philosophy, the simulation unit is the *Fleet*,
not an individual vehicle. FleetManager is the composition point that
exposes fleet-wide registries and fleet-level onboarding operations.

It delegates entity-specific bookkeeping to DriverManager,
VehicleManager, and TripManager rather than duplicating their state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from digital_twin.common.exceptions import (
    ConfigurationError,
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from digital_twin.config.simulation_config import FleetManagerConfig
from digital_twin.entities.driver import Driver
from digital_twin.entities.trip import Trip
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.managers.driver_manager import DriverManager
from digital_twin.managers.trip_manager import TripManager
from digital_twin.managers.vehicle_manager import VehicleManager

logger = logging.getLogger(__name__)


@dataclass
class ShiftRecord:
    """Minimal, persistent registry record for a driver's shift."""

    shift_id: str
    driver_id: str
    start_time: datetime
    end_time: datetime


class FleetManager:
    """Owns fleet-level coordination by composing specialized managers.

    FleetManager does not own driver, vehicle, or trip registries.
    Those registries remain owned by their respective managers.

    FleetManager owns the shift registry because no dedicated
    ShiftManager exists in the current sprint.
    """

    def __init__(
        self,
        config: FleetManagerConfig,
        driver_manager: DriverManager,
        vehicle_manager: VehicleManager,
        trip_manager: TripManager,
    ) -> None:
        self._config = config
        self._driver_manager = driver_manager
        self._vehicle_manager = vehicle_manager
        self._trip_manager = trip_manager
        self._shifts: dict[str, ShiftRecord] = {}

    @property
    def driver_manager(self) -> DriverManager:
        return self._driver_manager

    @property
    def vehicle_manager(self) -> VehicleManager:
        return self._vehicle_manager

    @property
    def trip_manager(self) -> TripManager:
        return self._trip_manager
    
    def onboard_driver(
        self,
        driver_id: str,
        name: str,
    )  -> Driver:
        """Create and register a simulated driver."""

        if len(self._driver_manager.list_drivers()) >= self._config.max_drivers:
            raise ConfigurationError(
                f"Fleet driver capacity ({self._config.max_drivers}) reached."
            )

        driver = Driver(
            driver_id=driver_id,
            name=name,
            license_number=f"SIM-LICENSE-{driver_id}",
        )

        return self._driver_manager.register_driver(driver)
    def onboard_vehicle(
        self,
        vehicle_id: str,
        vehicle_type: str,
    ) -> Vehicle:
        """Create and register a simulated vehicle."""

        if len(self._vehicle_manager.list_vehicles()) >= self._config.max_vehicles:
            raise ConfigurationError(
                f"Fleet vehicle capacity ({self._config.max_vehicles}) reached."
            )

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin=f"SIM-{vehicle_id}",
            specification=VehicleSpecification(
                manufacturer="Simulation",
                model=vehicle_type,
                year=2026,
                fuel_type=FuelType.DIESEL,
                transmission=TransmissionType.AUTOMATIC,
            ),
        )

        return self._vehicle_manager.register_vehicle(vehicle)

    def create_trip(
        self,
        trip_id: str,
        origin: str,
        destination: str,
        created_at: datetime,
    ) -> Trip:
        """Create a new trip request for the fleet."""

        return self._trip_manager.create_trip(
            trip_id=trip_id,
            origin=origin,
            destination=destination,
            created_at=created_at,
        )

    def schedule_shift(
        self,
        shift_id: str,
        driver_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> ShiftRecord:
        """Schedule a shift for a registered driver."""

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

        logger.info(
            "Scheduled shift %s for driver %s",
            shift_id,
            driver_id,
        )

        return record

    def get_shift(self, shift_id: str) -> ShiftRecord:
        """Look up a scheduled shift."""

        record = self._shifts.get(shift_id)

        if record is None:
            raise EntityNotFoundError("Shift", shift_id)

        return record

    def list_shifts_for_driver(
        self,
        driver_id: str,
    ) -> list[ShiftRecord]:
        """List all scheduled shifts belonging to a driver."""

        return [
            shift
            for shift in self._shifts.values()
            if shift.driver_id == driver_id
        ]

    def fleet_summary(self) -> dict[str, int]:
        """Return a fleet-wide registry summary."""

        return {
            "vehicle_count": len(self._vehicle_manager.list_vehicles()),
            "driver_count": len(self._driver_manager.list_drivers()),
            "active_trip_count": len(self._trip_manager.list_active_trips()),
            "shift_count": len(self._shifts),
        }