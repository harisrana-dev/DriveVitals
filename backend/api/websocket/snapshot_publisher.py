from asyncio import Queue

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)


class DashboardSnapshotPublisher:
    """
    Adapts the synchronous AnalyticsSnapshotStream
    to the asynchronous dashboard snapshot queue.
    """

    def __init__(
        self,
        queue: Queue[
            AnalyticsSnapshot
        ],
    ) -> None:

        self._queue = queue

    def publish(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        """
        Receive an AnalyticsSnapshot and enqueue it
        for asynchronous WebSocket broadcasting.
        """

        self._queue.put_nowait(
            snapshot
        )