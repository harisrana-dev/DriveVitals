"""
Driver Score Calculator.

Computes driver safety, aggression, and efficiency scores from
aggregated behaviour counters. Contains no aggregation logic — counts
are passed in.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from backend.analytics.driver_statistics.config import (
    AGGRESSION_MAX_DENSITY,
    AGGRESSION_WEIGHT_HARD_ACCELERATION,
    AGGRESSION_WEIGHT_HARD_BRAKE,
    AGGRESSION_WEIGHT_OVERSPEED,
    EFFICIENCY_MAX_EVENTS_PER_KM,
    SAFETY_HARD_ACCELERATION_PENALTY,
    SAFETY_HARD_BRAKE_PENALTY,
    SAFETY_OVERSPEED_PENALTY,
    SAFETY_START,
    clamp_score,
    events_per_km,
)


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

    Scoring model
    -------------
    Safety:
        Starts at 100 and deducts a fixed penalty per hard brake, hard
        acceleration, and overspeed event.
    Aggression:
        Rises with the weighted density of aggressive events per
        kilometre. The more aggressive events per distance, the higher
        the score.
    Efficiency:
        Starts at 100 and is reduced by the density of all behaviour
        events per kilometre, rewarding smooth trips with few events.
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
            Reserved for future score weighting configuration. Stored but
            not applied so no weighting semantics are guessed.
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

        Raises
        ------
        ValueError:
            If any count is negative or the total distance is negative.
        """
        self._validate(
            total_events=total_events,
            harsh_braking_count=harsh_braking_count,
            overspeed_count=overspeed_count,
            harsh_acceleration_count=harsh_acceleration_count,
            total_distance=total_distance,
            total_trips=total_trips,
        )

        safety_score = self._safety_score(
            harsh_braking_count=harsh_braking_count,
            harsh_acceleration_count=harsh_acceleration_count,
            overspeed_count=overspeed_count,
        )
        aggression_score = self._aggression_score(
            harsh_braking_count=harsh_braking_count,
            harsh_acceleration_count=harsh_acceleration_count,
            overspeed_count=overspeed_count,
            total_distance=total_distance,
        )
        efficiency_score = self._efficiency_score(
            total_events=total_events,
            total_distance=total_distance,
        )

        return DriverScores(
            safety_score=safety_score,
            aggression_score=aggression_score,
            efficiency_score=efficiency_score,
        )

    @staticmethod
    def _validate(
        *,
        total_events: int,
        harsh_braking_count: int,
        overspeed_count: int,
        harsh_acceleration_count: int,
        total_distance: float,
        total_trips: int,
    ) -> None:
        counts = (
            total_events,
            harsh_braking_count,
            overspeed_count,
            harsh_acceleration_count,
            total_trips,
        )
        if any(count < 0 for count in counts):
            raise ValueError("event and trip counts must be non-negative")
        if total_distance < 0.0:
            raise ValueError("total_distance must be non-negative")

    @staticmethod
    def _safety_score(
        *,
        harsh_braking_count: int,
        harsh_acceleration_count: int,
        overspeed_count: int,
    ) -> float:
        deductions = (
            harsh_braking_count * SAFETY_HARD_BRAKE_PENALTY
            + harsh_acceleration_count * SAFETY_HARD_ACCELERATION_PENALTY
            + overspeed_count * SAFETY_OVERSPEED_PENALTY
        )
        return clamp_score(SAFETY_START - deductions)

    @staticmethod
    def _aggression_score(
        *,
        harsh_braking_count: int,
        harsh_acceleration_count: int,
        overspeed_count: int,
        total_distance: float,
    ) -> float:
        weighted_events = (
            harsh_braking_count * AGGRESSION_WEIGHT_HARD_BRAKE
            + harsh_acceleration_count * AGGRESSION_WEIGHT_HARD_ACCELERATION
            + overspeed_count * AGGRESSION_WEIGHT_OVERSPEED
        )
        density = events_per_km(weighted_events, total_distance)
        return clamp_score(density / AGGRESSION_MAX_DENSITY * 100.0)

    @staticmethod
    def _efficiency_score(
        *,
        total_events: int,
        total_distance: float,
    ) -> float:
        density = events_per_km(total_events, total_distance)
        deduction = min(100.0, density / EFFICIENCY_MAX_EVENTS_PER_KM * 100.0)
        return clamp_score(100.0 - deduction)
