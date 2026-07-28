from asyncio import Queue

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.dashboard.schemas.dashboard_payload import (
    DashboardSnapshot,
)


class DashboardSnapshotPublisher:

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