from datetime import datetime

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.trips.schemas.trip_payload import (
    TripSnapshot,
)


class TripStore:
    def __init__(self) -> None:
        self._trips: dict[str, TripSnapshot] = {}

    def add(
        self,
        snapshot: TripSnapshot,
    ) -> None:
        # A completed trip is published exactly once; re-publishing
        # the same ``trip_id`` (e.g. a retry) must update the stored
        # snapshot instead of appending a duplicate. Dict keyed by
        # ``trip_id`` preserves insertion order for the trip list.
        self._trips[snapshot.trip_id] = snapshot

    def all(
        self,
    ) -> tuple[TripSnapshot, ...]:
        return tuple(self._trips.values())

    def clear(self) -> None:
        self._trips.clear()

    def __len__(self) -> int:
        return len(self._trips)
