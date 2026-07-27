from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)


class SnapshotSubscriber:
    """
    Basic subscriber for live analytics snapshots.

    This currently stores the latest snapshot per vehicle.

    Later, this will become the bridge to:
        - WebSocket broadcasting
        - dashboard updates
        - other live consumers
    """

    def __init__(self) -> None:

        self._latest: dict[
            str,
            AnalyticsSnapshot,
        ] = {}

    def consume(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        """
        Receive and store the latest snapshot.
        """

        self._latest[
            snapshot.vehicle_id
        ] = snapshot

    def get(
        self,
        vehicle_id: str,
    ) -> AnalyticsSnapshot | None:
        """
        Return the latest snapshot for one vehicle.
        """

        return self._latest.get(
            vehicle_id
        )

    def get_all(
        self,
    ) -> tuple[
        AnalyticsSnapshot,
        ...,
    ]:

        return tuple(
            self._latest.values()
        )