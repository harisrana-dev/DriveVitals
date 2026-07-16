"""TripManager: creates trips, ends trips, and maintains active/history registries.

Sprint 1 scope: trip lifecycle bookkeeping only. Route calculation,
ETA, and cargo modeling belong to future sprints (Entities/Physics).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from digital_twin.common.enums import ExecutionPhase, TripStatus
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


@dataclass
class TripRecord:
    """Minimal, persistent registry record for a single trip.

    Attributes:
        trip_id: Unique identifier for the trip.
        origin: Free-form origin label/address.
        destination: Free-form destination label/address.
        status: Current lifecycle status of the trip.
        driver_id: Id of the assigned driver, if any.
        vehicle_id: Id of the assigned vehicle, if any.
        created_at: Simulated time the trip was created.
        started_at: Simulated time the trip began, if started.
        ended_at: Simulated time the trip ended, if ended.
    """

    trip_id: str
    origin: str
    destination: str
    status: TripStatus = TripStatus.PENDING
    driver_id: str | None = None
    vehicle_id: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class TripManager:
    """Owns trip creation, lifecycle transitions, and history."""

    def __init__(self) -> None:
        """Initialize empty active and historical trip registries."""
        self._active_trips: dict[str, TripRecord] = {}
        self._trip_history: dict[str, TripRecord] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: TripManager runs during the TRIPS phase."""
        return ExecutionPhase.TRIPS

    def create_trip(
        self,
        trip_id: str,
        origin: str,
        destination: str,
        created_at: datetime,
    ) -> TripRecord:
        """Create a new pending trip.

        Args:
            trip_id: Unique id for the new trip.
            origin: Free-form origin label/address.
            destination: Free-form destination label/address.
            created_at: Simulated time of creation (typically the
                current tick's simulation_time).

        Returns:
            The newly created TripRecord.

        Raises:
            EntityAlreadyExistsError: If trip_id already exists in
                either the active or historical registries.
        """
        if trip_id in self._active_trips or trip_id in self._trip_history:
            raise EntityAlreadyExistsError("Trip", trip_id)
        record = TripRecord(
            trip_id=trip_id,
            origin=origin,
            destination=destination,
            created_at=created_at,
        )
        self._active_trips[trip_id] = record
        logger.info("Created trip %s: %s -> %s", trip_id, origin, destination)
        return record

    def assign_trip(self, trip_id: str, driver_id: str, vehicle_id: str) -> None:
        """Assign a driver and vehicle to a pending trip.

        Args:
            trip_id: Id of the trip to assign.
            driver_id: Id of the driver assigned.
            vehicle_id: Id of the vehicle assigned.

        Raises:
            EntityNotFoundError: If trip_id is not an active trip.
        """
        record = self._require_active(trip_id)
        record.driver_id = driver_id
        record.vehicle_id = vehicle_id
        record.status = TripStatus.ASSIGNED

    def start_trip(self, trip_id: str, started_at: datetime) -> None:
        """Transition an assigned trip to IN_PROGRESS.

        Args:
            trip_id: Id of the trip to start.
            started_at: Simulated time the trip started.

        Raises:
            EntityNotFoundError: If trip_id is not an active trip.
        """
        record = self._require_active(trip_id)
        record.status = TripStatus.IN_PROGRESS
        record.started_at = started_at

    def end_trip(self, trip_id: str, ended_at: datetime, cancelled: bool = False) -> TripRecord:
        """End a trip, moving it from active to historical registry.

        Args:
            trip_id: Id of the trip to end.
            ended_at: Simulated time the trip ended.
            cancelled: If True, marks the trip CANCELLED instead of
                COMPLETED.

        Returns:
            The finalized TripRecord, now stored in history.

        Raises:
            EntityNotFoundError: If trip_id is not an active trip.
        """
        record = self._require_active(trip_id)
        record.status = TripStatus.CANCELLED if cancelled else TripStatus.COMPLETED
        record.ended_at = ended_at
        del self._active_trips[trip_id]
        self._trip_history[trip_id] = record
        logger.info("Ended trip %s status=%s", trip_id, record.status.value)
        return record

    def get_trip(self, trip_id: str) -> TripRecord:
        """Look up a trip by id, checking active trips then history.

        Args:
            trip_id: Id of the trip to retrieve.

        Returns:
            The matching TripRecord.

        Raises:
            EntityNotFoundError: If trip_id exists in neither registry.
        """
        if trip_id in self._active_trips:
            return self._active_trips[trip_id]
        if trip_id in self._trip_history:
            return self._trip_history[trip_id]
        raise EntityNotFoundError("Trip", trip_id)

    def list_active_trips(self) -> list[TripRecord]:
        """List all currently active (non-terminal) trips.

        Returns:
            All TripRecord instances in the active registry.
        """
        return list(self._active_trips.values())

    def list_pending_trips(self) -> list[TripRecord]:
        """List active trips awaiting assignment.

        Returns:
            TripRecords whose status is PENDING.
        """
        return [t for t in self._active_trips.values() if t.status == TripStatus.PENDING]

    def list_trip_history(self) -> list[TripRecord]:
        """List all completed/cancelled trips.

        Returns:
            All TripRecord instances in the historical registry.
        """
        return list(self._trip_history.values())

    def on_tick(self, context: TickContext) -> None:
        """Per-tick hook for TripManager.

        Sprint 1 does not simulate trip progress (no physics/routing
        yet); this hook exists so TripManager satisfies the
        TickableManager protocol and future sprints can add progress
        tracking without changing the runtime.

        Args:
            context: The current tick's immutable context.
        """
        logger.debug("TripManager on_tick tick_id=%s (no-op)", context.tick_id)

    def _require_active(self, trip_id: str) -> TripRecord:
        """Look up an active trip or raise if it doesn't exist.

        Args:
            trip_id: Id to look up.

        Returns:
            The matching TripRecord from the active registry.

        Raises:
            EntityNotFoundError: If trip_id is not an active trip.
        """
        record = self._active_trips.get(trip_id)
        if record is None:
            raise EntityNotFoundError("Trip", trip_id)
        return record