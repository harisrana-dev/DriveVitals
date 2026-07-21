"""TripManager: creates trips, ends trips, and maintains active/history registries.

The manager owns trip lifecycle and registry concerns. The canonical
domain state is represented by ``digital_twin.entities.trip.Trip``.

Route calculation, ETA, physics, and cargo modeling belong to their
respective domain modules.
"""

from __future__ import annotations

import logging
from datetime import datetime

from digital_twin.common.enums import ExecutionPhase, TripStatus
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.entities.trip import Trip
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class TripManager:
    """Owns trip creation, lifecycle transitions, and historical records."""

    def __init__(self) -> None:
        """Initialize empty active and historical trip registries."""
        self._active_trips: dict[str, Trip] = {}
        self._trip_history: dict[str, Trip] = {}

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
    ) -> Trip:
        """Create and register a new pending Trip entity.

        Args:
            trip_id: Unique id for the new trip.
            origin: Origin label/address.
            destination: Destination label/address.
            created_at: Simulated creation timestamp.

        Returns:
            The newly created Trip entity.

        Raises:
            EntityAlreadyExistsError: If trip_id already exists.
        """
        if trip_id in self._active_trips or trip_id in self._trip_history:
            raise EntityAlreadyExistsError("Trip", trip_id)

        trip = Trip(
            trip_id=trip_id,
            start_time=created_at,
        )

        self._active_trips[trip_id] = trip

        logger.info(
            "Created trip %s: %s -> %s",
            trip_id,
            origin,
            destination,
        )

        return trip

    def assign_trip(
        self,
        trip_id: str,
        driver_id: str,
        vehicle_id: str,
    ) -> None:
       """Assign a driver and vehicle to a pending trip."""
       record = self._require_active(trip_id)

       if record.status != TripStatus.PENDING:
           raise ValueError(
               f"Trip '{trip_id}' cannot be assigned from status "
               f"'{record.status.value}'."
            )

       record.driver_id = driver_id
       record.vehicle_id = vehicle_id
       record.status = TripStatus.ASSIGNED

    def start_trip(
        self,
        trip_id: str,
        started_at: datetime,
    ) -> None:
       """Transition an assigned trip to IN_PROGRESS."""
       record = self._require_active(trip_id)

       if record.status != TripStatus.ASSIGNED:
           raise ValueError(
               f"Trip '{trip_id}' cannot start from status "
               f"'{record.status.value}'."
            )

       record.status = TripStatus.IN_PROGRESS
       record.started_at = started_at

       logger.info("Started trip %s", trip_id)

    def end_trip(
        self,
        trip_id: str,
        ended_at: datetime,
        cancelled: bool = False,
    ) -> Trip:
        """End a trip and move it to permanent historical storage.

        Args:
            trip_id: Id of the trip to end.
            ended_at: Simulated end timestamp.
            cancelled: If True, marks the trip as CANCELLED.

        Returns:
            The finalized Trip entity.

        Raises:
            EntityNotFoundError: If trip_id is not active.
        """
        trip = self._require_active(trip_id)

        trip.status = (
            TripStatus.CANCELLED
            if cancelled
            else TripStatus.COMPLETED
        )
        trip.end_time = ended_at

        del self._active_trips[trip_id]
        self._trip_history[trip_id] = trip

        logger.info(
            "Ended trip %s status=%s",
            trip_id,
            trip.status.value,
        )

        return trip

    def get_trip(self, trip_id: str) -> Trip:
        """Look up a trip in active or historical storage.

        Args:
            trip_id: Id of the trip to retrieve.

        Returns:
            The canonical Trip entity.

        Raises:
            EntityNotFoundError: If the trip does not exist.
        """
        if trip_id in self._active_trips:
            return self._active_trips[trip_id]

        if trip_id in self._trip_history:
            return self._trip_history[trip_id]

        raise EntityNotFoundError("Trip", trip_id)

    def list_active_trips(self) -> list[Trip]:
        """Return all currently active trips."""
        return list(self._active_trips.values())

    def list_pending_trips(self) -> list[Trip]:
        """Return active trips awaiting assignment."""
        return [
            trip
            for trip in self._active_trips.values()
            if trip.status == TripStatus.PENDING
        ]

    def list_trip_history(self) -> list[Trip]:
        """Return all completed and cancelled trips."""
        return list(self._trip_history.values())

    def on_tick(self, context: TickContext) -> None:
        """Per-tick hook for TripManager.

        Trip progress is currently handled by future simulation and
        physics layers. The manager only maintains lifecycle state.
        """
        logger.debug(
            "TripManager on_tick tick_id=%s (no-op)",
            context.tick_id,
        )

    def _require_active(self, trip_id: str) -> Trip:
        """Look up an active trip or raise an error."""
        trip = self._active_trips.get(trip_id)

        if trip is None:
            raise EntityNotFoundError("Trip", trip_id)

        return trip