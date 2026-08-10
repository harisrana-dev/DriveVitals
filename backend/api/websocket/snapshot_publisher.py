from asyncio import Queue

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.dashboard.schemas.dashboard_payload import (
    DashboardSnapshot,
)


class DashboardSnapshotPublisher:
    """Subscriber to ``AnalyticsSnapshotStream`` that bridges synchronous
    analytics output into the asynchronous WebSocket delivery layer.

    Each incoming ``AnalyticsSnapshot`` is converted into a
    ``DashboardSnapshot`` via the injected builder and placed onto the
    provided ``asyncio.Queue``. This is the sync-to-async adaptation
    point for the dashboard channel.
    """

    def __init__(
        self,
        queue: Queue[DashboardSnapshot],
        builder,
    ) -> None:

        self._queue = queue
        self._builder = builder


    def publish(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:

        dashboard_snapshot = (
            self._builder.update(snapshot)
        )

        self._queue.put_nowait(
            dashboard_snapshot
        )