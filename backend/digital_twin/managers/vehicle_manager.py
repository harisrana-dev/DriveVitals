"""VehicleManager: owns vehicle lifecycle, lookup, and availability.

Sprint 1 scope: this manager tracks registry-level vehicle state
(status and assignment) only.

Physics, wear, fuel, telemetry, and operating state updates belong to
future Physics and Telemetry modules.
"""

from __future__ import annotations

import logging

from digital_twin.common.enums import ExecutionPhase, VehicleStatus
from digital_twin.common.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from digital_twin.entities.vehicle import Vehicle
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class VehicleManager:
    """Owns the registry of active vehicles and their availability state."""

    def __init__(self) -> None:
        """Initialize an empty vehicle registry."""
        self._vehicles: dict[str, Vehicle] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: VehicleManager runs during the VEHICLES phase."""
        return ExecutionPhase.VEHICLES

    def register_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """Register a vehicle entity in the fleet."""
        if vehicle.vehicle_id in self._vehicles:
            raise EntityAlreadyExistsError("Vehicle", vehicle.vehicle_id)

        self._vehicles[vehicle.vehicle_id] = vehicle

        logger.info(
            "Registered vehicle %s (%s %s)",
            vehicle.vehicle_id,
            vehicle.specification.manufacturer,
            vehicle.specification.model,
        )

        return vehicle

    def deregister_vehicle(self, vehicle_id: str) -> None:
        """Remove a vehicle from the registry permanently."""
        self._require(vehicle_id)

        del self._vehicles[vehicle_id]

        logger.info("Deregistered vehicle %s", vehicle_id)

    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        """Look up a vehicle by ID."""
        return self._require(vehicle_id)

    def list_vehicles(self) -> list[Vehicle]:
        """List all registered vehicles."""
        return list(self._vehicles.values())

    def list_available_vehicles(self) -> list[Vehicle]:
        """List vehicles currently available for assignment."""
        return [
            vehicle
            for vehicle in self._vehicles.values()
            if vehicle.status == VehicleStatus.AVAILABLE
        ]

    def set_status(
        self,
        vehicle_id: str,
        status: VehicleStatus,
    ) -> None:
        """Update a vehicle's lifecycle status."""
        vehicle = self._require(vehicle_id)

        logger.debug(
            "Vehicle %s status %s -> %s",
            vehicle_id,
            vehicle.status,
            status,
        )

        vehicle.status = status

    def assign(
        self,
        vehicle_id: str,
        driver_id: str,
        trip_id: str,
    ) -> None:
        """Assign a vehicle to a driver and trip."""
        vehicle = self._require(vehicle_id)

        vehicle.current_driver_id = driver_id
        vehicle.current_trip_id = trip_id
        vehicle.status = VehicleStatus.ASSIGNED

    def release(self, vehicle_id: str) -> None:
        """Clear a vehicle's assignment and return it to AVAILABLE."""
        vehicle = self._require(vehicle_id)

        vehicle.current_driver_id = None
        vehicle.current_trip_id = None
        vehicle.status = VehicleStatus.AVAILABLE

    def is_available(self, vehicle_id: str) -> bool:
        """Check whether a vehicle is currently available."""
        return self._require(vehicle_id).status == VehicleStatus.AVAILABLE

    def on_tick(self, context: TickContext) -> None:
        """Per-tick hook for future vehicle behavior."""
        logger.debug(
            "VehicleManager on_tick tick_id=%s (no-op)",
            context.tick_id,
        )

    def _require(self, vehicle_id: str) -> Vehicle:
        """Look up a vehicle or raise if it does not exist."""
        vehicle = self._vehicles.get(vehicle_id)

        if vehicle is None:
            raise EntityNotFoundError("Vehicle", vehicle_id)

        return vehicle