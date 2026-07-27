from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)


class WebSocketSnapshotSubscriber:
    """
    Bridges synchronous analytics snapshots
    into the asynchronous dashboard WebSocket queue.
    """

    def __init__(
        self,
        queue,
    ) -> None:

        self._queue = queue

    def consume(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:

        self._queue.put_nowait(
            snapshot
        )