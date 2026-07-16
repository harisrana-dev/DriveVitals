"""VehicleManager: owns vehicle lifecycle, lookup, and availability.

Sprint 1 scope: this manager tracks *registry-level* vehicle state
(status, assignment) only. It does not model physics, wear, or fuel --
that belongs to the future `entities/` and `physics/` modules. The
`VehicleRecord` defined here is a deliberately minimal placeholder that
Sprint 2 is expected to replace/extend with a full `Vehicle` entity
(see module docstring in digital_twin_runtime.py for the plug-in plan).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from digital_twin.common.enums import ExecutionPhase, VehicleStatus
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


@dataclass
class VehicleRecord:
    """Minimal, persistent registry record for a single vehicle.

    Attributes:
        vehicle_id: Unique identifier for the vehicle.
        vehicle_type: Free-form vehicle type/class label (e.g.
            "delivery_van", "city_car"). Sprint 2's Entity/Profile
            layer will formalize this into an enum/profile.
        status: Current lifecycle/availability status.
        assigned_driver_id: Id of the driver currently assigned, if any.
        assigned_trip_id: Id of the trip currently assigned, if any.
        odometer_km: Cumulative distance driven, persists across ticks.
    """

    vehicle_id: str
    vehicle_type: str
    status: VehicleStatus = VehicleStatus.AVAILABLE
    assigned_driver_id: str | None = None
    assigned_trip_id: str | None = None
    odometer_km: float = 0.0


class VehicleManager:
    """Owns the registry of active vehicles and their availability state.

    Responsible only for lifecycle/status/assignment bookkeeping. No
    physics, wear, or fuel modeling happens here -- see module
    docstring.
    """

    def __init__(self) -> None:
        """Initialize an empty vehicle registry."""
        self._vehicles: dict[str, VehicleRecord] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: VehicleManager runs during the VEHICLES phase."""
        return ExecutionPhase.VEHICLES

    def register_vehicle(self, vehicle_id: str, vehicle_type: str) -> VehicleRecord:
        """Register a new vehicle in the fleet.

        Args:
            vehicle_id: Unique id for the new vehicle.
            vehicle_type: Vehicle type/class label.

        Returns:
            The newly created VehicleRecord.

        Raises:
            EntityAlreadyExistsError: If vehicle_id is already registered.
        """
        if vehicle_id in self._vehicles:
            raise EntityAlreadyExistsError("Vehicle", vehicle_id)
        record = VehicleRecord(vehicle_id=vehicle_id, vehicle_type=vehicle_type)
        self._vehicles[vehicle_id] = record
        logger.info("Registered vehicle %s (%s)", vehicle_id, vehicle_type)
        return record

    def deregister_vehicle(self, vehicle_id: str) -> None:
        """Remove a vehicle from the registry permanently.

        Args:
            vehicle_id: Id of the vehicle to remove.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        self._require(vehicle_id)
        del self._vehicles[vehicle_id]
        logger.info("Deregistered vehicle %s", vehicle_id)

    def get_vehicle(self, vehicle_id: str) -> VehicleRecord:
        """Look up a vehicle by id.

        Args:
            vehicle_id: Id of the vehicle to retrieve.

        Returns:
            The matching VehicleRecord.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        return self._require(vehicle_id)

    def list_vehicles(self) -> list[VehicleRecord]:
        """List all registered vehicles.

        Returns:
            All VehicleRecord instances currently in the registry.
        """
        return list(self._vehicles.values())

    def list_available_vehicles(self) -> list[VehicleRecord]:
        """List vehicles currently available for assignment.

        Returns:
            VehicleRecords whose status is AVAILABLE.
        """
        return [v for v in self._vehicles.values() if v.status == VehicleStatus.AVAILABLE]

    def set_status(self, vehicle_id: str, status: VehicleStatus) -> None:
        """Update a vehicle's lifecycle status.

        Args:
            vehicle_id: Id of the vehicle to update.
            status: New status to set.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        record = self._require(vehicle_id)
        logger.debug("Vehicle %s status %s -> %s", vehicle_id, record.status, status)
        record.status = status

    def assign(self, vehicle_id: str, driver_id: str, trip_id: str) -> None:
        """Mark a vehicle as assigned to a driver and trip.

        Args:
            vehicle_id: Id of the vehicle being assigned.
            driver_id: Id of the driver it is assigned to.
            trip_id: Id of the trip it is assigned to.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        record = self._require(vehicle_id)
        record.assigned_driver_id = driver_id
        record.assigned_trip_id = trip_id
        record.status = VehicleStatus.ASSIGNED

    def release(self, vehicle_id: str) -> None:
        """Clear a vehicle's assignment and return it to AVAILABLE.

        Args:
            vehicle_id: Id of the vehicle to release.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        record = self._require(vehicle_id)
        record.assigned_driver_id = None
        record.assigned_trip_id = None
        record.status = VehicleStatus.AVAILABLE

    def is_available(self, vehicle_id: str) -> bool:
        """Check whether a vehicle is currently available for assignment.

        Args:
            vehicle_id: Id of the vehicle to check.

        Returns:
            True if the vehicle's status is AVAILABLE.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        return self._require(vehicle_id).status == VehicleStatus.AVAILABLE

    def on_tick(self, context: TickContext) -> None:
        """Per-tick hook for VehicleManager.

        Sprint 1 performs no per-tick vehicle behavior (no physics/wear
        yet); this hook exists so VehicleManager satisfies the
        TickableManager protocol and future sprints have a place to add
        odometer/wear updates without changing the runtime.

        Args:
            context: The current tick's immutable context.
        """
        logger.debug("VehicleManager on_tick tick_id=%s (no-op)", context.tick_id)

    def _require(self, vehicle_id: str) -> VehicleRecord:
        """Look up a vehicle or raise if it doesn't exist.

        Args:
            vehicle_id: Id to look up.

        Returns:
            The matching VehicleRecord.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        record = self._vehicles.get(vehicle_id)
        if record is None:
            raise EntityNotFoundError("Vehicle", vehicle_id)
        return record