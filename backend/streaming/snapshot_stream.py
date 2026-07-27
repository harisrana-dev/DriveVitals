from typing import Protocol

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)


class AnalyticsSnapshotSubscriber(Protocol):
    """
    Anything that wants to receive live analytics snapshots.
    """

    def publish(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        ...


class AnalyticsSnapshotStream:
    """
    Distributes AnalyticsSnapshot objects to subscribers.

    The stream does not know about:
        - FastAPI
        - WebSockets
        - databases
        - frontend clients

    It only distributes snapshots.
    """

    def __init__(self) -> None:
        self._subscribers: list[
            AnalyticsSnapshotSubscriber
        ] = []

    def subscribe(
        self,
        subscriber: AnalyticsSnapshotSubscriber,
    ) -> None:
        if subscriber not in self._subscribers:
            self._subscribers.append(
                subscriber
            )

    def unsubscribe(
        self,
        subscriber: AnalyticsSnapshotSubscriber,
    ) -> None:
        if subscriber in self._subscribers:
            self._subscribers.remove(
                subscriber
            )

    def publish(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        for subscriber in self._subscribers:
            subscriber.publish(
                snapshot
            )

    @property
    def subscriber_count(
        self,
    ) -> int:
        return len(
            self._subscribers
        )