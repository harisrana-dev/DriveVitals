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
        self._trips: list[TripSnapshot] = []

    def add(
        self,
        snapshot: TripSnapshot,
    ) -> None:
        self._trips.append(snapshot)

    def all(
        self,
    ) -> tuple[TripSnapshot, ...]:
        return tuple(self._trips)

    def clear(self) -> None:
        self._trips.clear()

    def __len__(self) -> int:
        return len(self._trips)
