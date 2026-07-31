"""
Driver Score Calculator.

Computes driver safety, aggression, and efficiency scores from
aggregated behaviour counters. Contains no aggregation logic — counts
are passed in.
"""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DriverScores:
    """
    Purpose:
        Carry the three driver scores produced by DriverScoreCalculator.
    Inputs:
        Produced by DriverScoreCalculator.calculate.
    Outputs:
        Consumed by DriverStatisticsEngine when building
        DriverStatistics.
    """

    safety_score: float
    aggression_score: float
    efficiency_score: float


class DriverScoreCalculator:
    """
    Purpose:
        Derive driver scores from aggregated behaviour counters.
    Inputs:
        Aggregated event counts and trip totals.
    Outputs:
        A DriverScores object.
    TODO:
        Define scoring formulas in a future milestone.
    """

    def __init__(
        self,
        *,
        weights: Mapping[str, float] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        weights:
            Future score weighting configuration. Intentionally left
            undefined in this milestone so no weights are guessed.
        """
        self._weights = weights

    def calculate(
        self,
        *,
        total_events: int,
        harsh_braking_count: int,
        overspeed_count: int,
        harsh_acceleration_count: int,
        total_distance: float,
        total_trips: int,
    ) -> DriverScores:
        """
        Compute safety, aggression, and efficiency scores.

        TODO: Implement scoring formulas from the aggregated counters.
        """
        raise NotImplementedError
