from asyncio import Queue

from datetime import datetime

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.trips.schemas.trip_payload import (
    TripSnapshot,
    TripsSnapshot,
)


class TripSnapshotPublisher:
    def __init__(
        self,
        queue: Queue[TripsSnapshot],
        builder,
        store,
    ) -> None:
        self._queue = queue
        self._builder = builder
        self._store = store

    def publish(
        self,
        summary: DriverBehaviourSummary,
        context,
        runtime_state,
        events: list,
        trip,
    ) -> None:
        trip_snapshot = self._builder.build(
            summary=summary,
            context=context,
            runtime_state=runtime_state,
            events=events,
            trip=trip,
        )
        self._store.add(trip_snapshot)
        trips = self._store.all()
        total = len(trips)
        total_distance = sum(t.distance_km for t in trips)
        total_fuel = sum(t.fuel_consumed_liters for t in trips)
        avg_score = (
            sum(t.safety_score for t in trips) / total
            if total > 0
            else 0.0
        )
        trips_snapshot = TripsSnapshot(
            timestamp=trip_snapshot.completed_at or trip_snapshot.started_at,
            trips=trips,
            total_trips=total,
            total_distance_km=total_distance,
            average_safety_score=avg_score,
            total_fuel_consumed_liters=total_fuel,
        )
        self._queue.put_nowait(trips_snapshot)

    def publish_active(
        self,
        snapshots: list[TripSnapshot],
        timestamp: datetime,
    ) -> None:
        """
        Broadcast the current active-trip set without touching the
        completed-trip store.

        Active trips are never added to ``TripStore``; this keeps the
        per-tick broadcast bounded to the live fleet (at most one
        snapshot per active vehicle) instead of replaying the entire
        completed-trip history on every tick.
        """

        trips = tuple(snapshots)
        total = len(trips)

        scores = [
            t.safety_score
            for t in trips
            if t.safety_score is not None
        ]
        total_distance = sum(t.distance_km for t in trips)
        total_fuel = sum(
            t.fuel_consumed_liters
            for t in trips
            if t.fuel_consumed_liters is not None
        )

        trips_snapshot = TripsSnapshot(
            timestamp=timestamp,
            trips=trips,
            total_trips=total,
            total_distance_km=total_distance,
            average_safety_score=(
                sum(scores) / len(scores)
                if scores
                else 0.0
            ),
            total_fuel_consumed_liters=total_fuel,
        )
        self._queue.put_nowait(trips_snapshot)
