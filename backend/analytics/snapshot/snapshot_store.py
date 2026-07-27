from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)


class AnalyticsSnapshotStore:
    """
    In-memory store for the latest analytics snapshot per vehicle.

    This represents live state.

    It is NOT historical persistence.
    """

    def __init__(self) -> None:
        self._latest: dict[
            str,
            AnalyticsSnapshot,
        ] = {}

    def update(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> None:
        """
        Store the latest snapshot for a vehicle.
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
    ) -> tuple[AnalyticsSnapshot, ...]:
        """
        Return the latest snapshot for every vehicle.
        """

        return tuple(
            self._latest.values()
        )

    def remove(
        self,
        vehicle_id: str,
    ) -> None:
        """
        Remove the latest snapshot for a vehicle.
        """

        self._latest.pop(
            vehicle_id,
            None,
        )

    def clear(self) -> None:
        """
        Remove all latest snapshots.
        """

        self._latest.clear()

    def __len__(self) -> int:
        return len(self._latest)