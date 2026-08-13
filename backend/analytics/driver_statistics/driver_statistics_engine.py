"""
Driver Statistics Engine.

Aggregates behaviour events and trip information into per-driver
statistics. The engine owns aggregation only — scoring is delegated to
the DriverScoreCalculator.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.driver_statistics.aggregators.driver_score_calculator import (
    DriverScoreCalculator,
)
from backend.analytics.driver_statistics.config import (
    EVENT_TYPE_AGGRESSIVE_THROTTLE,
    EVENT_TYPE_HARSH_BRAKING,
    EVENT_TYPE_HIGH_RPM,
    EVENT_TYPE_SPEEDING,
    KNOWN_EVENT_TYPES,
    KNOWN_SEVERITIES,
)
from backend.analytics.driver_statistics.models.driver_statistics import (
    DriverStatistics,
)
from backend.fleet.models.trip import Trip


def _trip_duration_seconds(trip: Trip) -> int:
    """Duration of a completed trip, or 0 when timestamps are missing."""
    if trip.started_at is None or trip.completed_at is None:
        return 0
    return int((trip.completed_at - trip.started_at).total_seconds())


def _average(values: list[float]) -> Optional[float]:
    """Arithmetic mean of non-empty values, else None."""
    if not values:
        return None
    return round(sum(values) / len(values), 2)


@dataclass(frozen=True, slots=True)
class _EventCounters:
    """
    Private aggregation of behaviour event counts for one driver.
    """

    total_events: int
    harsh_braking_count: int
    overspeed_count: int
    harsh_acceleration_count: int
    high_rpm_count: int


class DriverStatisticsEngine:
    """
    Purpose:
        Aggregate behaviour events and trips into DriverStatistics.
    Inputs:
        Behaviour events and trips for one driver.
    Outputs:
        A DriverStatistics object.
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

        Aggregates event counts and trip totals, then delegates scoring
        to the DriverScoreCalculator.

        The iterables are materialised once up front so the result is
        deterministic regardless of the iterable's source.

        Raises
        ------
        ValueError:
            If the driver_id is missing, a trip distance or duration is
            negative, or a behaviour event is invalid.
        """
        trips = tuple(trips)
        behaviour_events = tuple(behaviour_events)

        self._validate_driver_id(driver_id)
        self._validate_trips(trips)
        self._validate_events(behaviour_events)

        total_trips = len(trips)
        total_distance = sum(trip.distance_travelled_km for trip in trips)
        total_driving_time_seconds = sum(
            _trip_duration_seconds(trip) for trip in trips
        )
        total_fuel_used_liters = sum(
            trip.fuel_used_liters for trip in trips
        )
        scored_trips = [
            trip.trip_score
            for trip in trips
            if trip.trip_score is not None
        ]
        counters = self._aggregate_events(behaviour_events)

        scores = self._score_calculator.calculate(
            total_events=counters.total_events,
            harsh_braking_count=counters.harsh_braking_count,
            overspeed_count=counters.overspeed_count,
            harsh_acceleration_count=counters.harsh_acceleration_count,
            high_rpm_count=counters.high_rpm_count,
            total_distance=total_distance,
            total_trips=total_trips,
        )

        return DriverStatistics(
            driver_id=driver_id,
            safety_score=scores.safety_score,
            aggression_score=scores.aggression_score,
            efficiency_score=scores.efficiency_score,
            total_events=counters.total_events,
            harsh_braking_count=counters.harsh_braking_count,
            overspeed_count=counters.overspeed_count,
            harsh_acceleration_count=counters.harsh_acceleration_count,
            high_rpm_count=counters.high_rpm_count,
            total_distance=total_distance,
            total_trips=total_trips,
            total_driving_time_seconds=total_driving_time_seconds,
            total_fuel_used_liters=total_fuel_used_liters,
            average_trip_score=_average(
                scored_trips
            ),
            fuel_efficiency=(
                round(total_distance / total_fuel_used_liters, 2)
                if total_fuel_used_liters > 0
                else None
            ),
        )

    @staticmethod
    def _validate_driver_id(driver_id: str) -> None:
        if not isinstance(driver_id, str) or not driver_id.strip():
            raise ValueError("driver_id is required")

    @staticmethod
    def _validate_trips(trips: tuple[Trip, ...]) -> None:
        for trip in trips:
            if trip.distance_travelled_km < 0.0:
                raise ValueError(
                    f"trip '{trip.trip_id}' has negative distance"
                )
            if (
                trip.started_at is not None
                and trip.completed_at is not None
                and trip.completed_at < trip.started_at
            ):
                raise ValueError(
                    f"trip '{trip.trip_id}' has negative duration"
                )

    @staticmethod
    def _validate_events(events: tuple[BehaviourEvent, ...]) -> None:
        for event in events:
            if event.event_type not in KNOWN_EVENT_TYPES:
                raise ValueError(
                    f"unknown behaviour event type '{event.event_type}'"
                )
            if event.severity not in KNOWN_SEVERITIES:
                raise ValueError(
                    f"unknown behaviour event severity '{event.severity}'"
                )
            if event.distance_km < 0.0:
                raise ValueError(
                    f"behaviour event '{event.trip_id}/{event.event_type}' "
                    "has negative distance"
                )
            if event.duration_seconds < 0.0:
                raise ValueError(
                    f"behaviour event '{event.trip_id}/{event.event_type}' "
                    "has negative duration"
                )

    @staticmethod
    def _aggregate_events(
        events: tuple[BehaviourEvent, ...],
    ) -> _EventCounters:
        return _EventCounters(
            total_events=len(events),
            harsh_braking_count=sum(
                event.event_type == EVENT_TYPE_HARSH_BRAKING
                for event in events
            ),
            overspeed_count=sum(
                event.event_type == EVENT_TYPE_SPEEDING
                for event in events
            ),
            harsh_acceleration_count=sum(
                event.event_type == EVENT_TYPE_AGGRESSIVE_THROTTLE
                for event in events
            ),
            high_rpm_count=sum(
                event.event_type == EVENT_TYPE_HIGH_RPM
                for event in events
            ),
        )

    @property
    def score_calculator(self) -> DriverScoreCalculator:
        return self._score_calculator
