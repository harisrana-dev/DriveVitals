"""
IntelligenceState.

In-memory store for the latest fleet intelligence outputs produced by
the application consumers (VehicleHealthConsumer and
DriverStatisticsConsumer).

This represents live state.

It is NOT historical persistence.
"""

from backend.analytics.driver_statistics.models.driver_statistics import (
    DriverStatistics,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)


class IntelligenceState:
    """
    Purpose:
        Store the latest HealthSnapshot per vehicle and the latest
        DriverStatistics per driver.
    Inputs:
        Written by the fleet intelligence consumers.
    Outputs:
        Read by application layers that surface live intelligence state.
    """

    def __init__(self) -> None:
        self._health_snapshots: dict[
            str,
            HealthSnapshot,
        ] = {}
        self._driver_statistics: dict[
            str,
            DriverStatistics,
        ] = {}

    def update_health_snapshot(
        self,
        snapshot: HealthSnapshot,
    ) -> None:
        """
        Store the latest health snapshot for a vehicle.
        """

        self._health_snapshots[
            snapshot.vehicle_id
        ] = snapshot

    def get_health_snapshot(
        self,
        vehicle_id: str,
    ) -> HealthSnapshot | None:
        """
        Return the latest health snapshot for one vehicle.
        """

        return self._health_snapshots.get(
            vehicle_id
        )

    def get_all_health_snapshots(
        self,
    ) -> tuple[HealthSnapshot, ...]:
        """
        Return the latest health snapshot for every vehicle.
        """

        return tuple(
            self._health_snapshots.values()
        )

    def update_driver_statistics(
        self,
        statistics: DriverStatistics,
    ) -> None:
        """
        Store the latest driver statistics for a driver.
        """

        self._driver_statistics[
            statistics.driver_id
        ] = statistics

    def get_driver_statistics(
        self,
        driver_id: str,
    ) -> DriverStatistics | None:
        """
        Return the latest driver statistics for one driver.
        """

        return self._driver_statistics.get(
            driver_id
        )

    def get_all_driver_statistics(
        self,
    ) -> tuple[DriverStatistics, ...]:
        """
        Return the latest driver statistics for every driver.
        """

        return tuple(
            self._driver_statistics.values()
        )

    def clear(self) -> None:
        """
        Remove all intelligence state.
        """

        self._health_snapshots.clear()
        self._driver_statistics.clear()

    def __len__(self) -> int:
        return (
            len(self._health_snapshots)
            + len(self._driver_statistics)
        )
