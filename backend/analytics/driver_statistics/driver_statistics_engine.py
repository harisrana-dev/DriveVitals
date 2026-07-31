"""
Driver Statistics Engine.

Aggregates behaviour events and trip information into per-driver
statistics. The engine owns aggregation only — scoring is delegated to
the DriverScoreCalculator.
"""

from collections.abc import Iterable

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.driver_statistics.aggregators.driver_score_calculator import (
    DriverScoreCalculator,
)
from backend.analytics.driver_statistics.models.driver_statistics import (
    DriverStatistics,
)
from backend.fleet.models.trip import Trip


class DriverStatisticsEngine:
    """
    Purpose:
        Aggregate behaviour events and trips into DriverStatistics.
    Inputs:
        Behaviour events and trips for one driver.
    Outputs:
        A DriverStatistics object.
    TODO:
        Decide whether results should be cached per driver and how
        updates are triggered (trip completion vs. periodic).
    """

    def __init__(
        self,
        *,
        score_calculator: DriverScoreCalculator,
    ) -> None:
        self._score_calculator = score_calculator

    def compute_statistics(
        self,
        *,
        driver_id: str,
        behaviour_events: Iterable[BehaviourEvent],
        trips: Iterable[Trip],
    ) -> DriverStatistics:
        """
        Compute a driver's aggregated statistics.

        TODO: Implement. Aggregates event counts and trip totals, then
        delegates scoring to the DriverScoreCalculator.
        """
        raise NotImplementedError

    @property
    def score_calculator(self) -> DriverScoreCalculator:
        return self._score_calculator
