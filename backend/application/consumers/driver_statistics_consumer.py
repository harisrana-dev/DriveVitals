"""
DriverStatisticsConsumer.

Application consumer that bridges trip completion data (the BehaviourEvents
collected during a trip plus the completed Trip) into the
DriverStatisticsEngine and retains the latest DriverStatistics per
driver in the IntelligenceState.
"""

import logging

from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.driver_statistics.driver_statistics_engine import (
    DriverStatisticsEngine,
)
from backend.analytics.driver_statistics.models.driver_statistics import (
    DriverStatistics,
)
from backend.application.intelligence_state import (
    IntelligenceState,
)
from backend.fleet.models.trip import (
    Trip,
)

logger = logging.getLogger(__name__)


class DriverStatisticsConsumer:
    """
    Purpose:
        Aggregate completed-trip behaviour events and trips into
        per-driver statistics.
    Inputs:
        BehaviourEvents and a Trip for one driver.
    Outputs:
        Latest DriverStatistics per driver in the IntelligenceState.
    """

    def __init__(
        self,
        *,
        engine: DriverStatisticsEngine,
        state: IntelligenceState,
    ) -> None:
        self._engine = engine
        self._state = state
        self._events_by_driver: dict[
            str,
            list[BehaviourEvent],
        ] = {}
        self._trips_by_driver: dict[
            str,
            list[Trip],
        ] = {}

    def seed(
        self,
        *,
        driver_id: str,
        behaviour_events: list[BehaviourEvent],
        trips: list[Trip],
    ) -> None:
        """
        Seed the accumulator with persisted history before the runtime
        produces new trips.

        Replaces any prior session state so a freshly started runtime
        continues aggregating over the full recorded history instead of
        starting from zero.
        """

        self._events_by_driver[driver_id] = list(behaviour_events)
        self._trips_by_driver[driver_id] = list(trips)

    def record_trip(
        self,
        *,
        driver_id: str,
        behaviour_events: list[BehaviourEvent],
        trip: Trip,
    ) -> DriverStatistics:
        """
        Record one completed trip and recompute the driver's statistics.

        Behaviour events and trips accumulate per driver across trips.
        """

        self._events_by_driver.setdefault(
            driver_id,
            [],
        ).extend(
            behaviour_events
        )

        self._trips_by_driver.setdefault(
            driver_id,
            [],
        ).append(
            trip
        )

        statistics = (
            self._engine.compute_statistics(
                driver_id=driver_id,
                behaviour_events=self._events_by_driver[driver_id],
                trips=self._trips_by_driver[driver_id],
            )
        )

        self._state.update_driver_statistics(
            statistics
        )

        return statistics

    def get_latest(
        self,
        driver_id: str,
    ) -> DriverStatistics | None:
        """
        Return the latest DriverStatistics for one driver.
        """

        return self._state.get_driver_statistics(
            driver_id
        )
