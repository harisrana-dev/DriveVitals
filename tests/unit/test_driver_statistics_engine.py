"""Unit tests for the DriverStatisticsEngine trip-metric aggregation.

Covers the fields introduced for the driver page: total driving time,
total fuel used, average trip score (from real trip scores only) and
fuel efficiency (never fabricated when no fuel is measured), plus the
real high-rpm count carried through to the statistics.
"""

from datetime import datetime, timedelta, timezone

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.driver_statistics.driver_statistics_engine import (
    DriverStatisticsEngine,
)
from backend.analytics.driver_statistics.aggregators.driver_score_calculator import (
    DriverScoreCalculator,
)
from backend.fleet.models.trip import Trip


def _make_engine() -> DriverStatisticsEngine:
    return DriverStatisticsEngine(
        score_calculator=DriverScoreCalculator(),
    )


def _make_trip(
    trip_id: str,
    driver_id: str,
    *,
    distance_km: float,
    fuel_liters: float = 0.0,
    trip_score: float | None = None,
    duration_minutes: int = 0,
) -> Trip:
    start = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    return Trip(
        trip_id=trip_id,
        vehicle_id="v-1",
        driver_id=driver_id,
        route_id="r-1",
        started_at=start,
        completed_at=start + timedelta(minutes=duration_minutes),
        distance_travelled_km=distance_km,
        fuel_used_liters=fuel_liters,
        trip_score=trip_score,
    )


def _make_event(
    driver_id: str,
    trip_id: str,
    event_type: str,
) -> BehaviourEvent:
    ts = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    return BehaviourEvent(
        vehicle_id="v-1",
        driver_id=driver_id,
        trip_id=trip_id,
        event_type=event_type,
        started_at=ts,
        ended_at=ts,
        duration_seconds=5.0,
        distance_km=0.1,
        severity="moderate",
    )


class TestTripMetricAggregation:
    def test_aggregates_duration_fuel_and_trip_scores(self) -> None:
        engine = _make_engine()
        trips = (
            _make_trip(
                "t-1",
                "d-1",
                distance_km=50.0,
                fuel_liters=4.0,
                trip_score=80.0,
                duration_minutes=30,
            ),
            _make_trip(
                "t-2",
                "d-1",
                distance_km=50.0,
                fuel_liters=6.0,
                trip_score=70.0,
                duration_minutes=30,
            ),
        )

        stats = engine.compute_statistics(
            driver_id="d-1",
            behaviour_events=(),
            trips=trips,
        )

        assert stats.total_distance == 100.0
        assert stats.total_trips == 2
        assert stats.total_driving_time_seconds == 3600
        assert stats.total_fuel_used_liters == 10.0
        assert stats.average_trip_score == 75.0
        assert stats.fuel_efficiency == 10.0

    def test_no_fuel_means_no_fabricated_efficiency(self) -> None:
        engine = _make_engine()
        trips = (
            _make_trip("t-1", "d-1", distance_km=50.0),
            _make_trip("t-2", "d-1", distance_km=50.0),
        )

        stats = engine.compute_statistics(
            driver_id="d-1",
            behaviour_events=(),
            trips=trips,
        )

        assert stats.total_driving_time_seconds == 0
        assert stats.total_fuel_used_liters == 0.0
        assert stats.fuel_efficiency is None
        assert stats.average_trip_score is None

    def test_unscored_trips_excluded_from_average(self) -> None:
        engine = _make_engine()
        trips = (
            _make_trip(
                "t-1",
                "d-1",
                distance_km=25.0,
                trip_score=90.0,
            ),
            _make_trip("t-2", "d-1", distance_km=25.0),
        )

        stats = engine.compute_statistics(
            driver_id="d-1",
            behaviour_events=(),
            trips=trips,
        )

        assert stats.average_trip_score == 90.0

    def test_high_rpm_count_is_carried_through(self) -> None:
        engine = _make_engine()
        events = (
            _make_event("d-1", "t-1", "high_rpm"),
            _make_event("d-1", "t-1", "high_rpm"),
            _make_event("d-1", "t-1", "speeding"),
        )

        stats = engine.compute_statistics(
            driver_id="d-1",
            behaviour_events=events,
            trips=(_make_trip("t-1", "d-1", distance_km=10.0),),
        )

        assert stats.high_rpm_count == 2
        assert stats.total_events == 3
        assert stats.overspeed_count == 1
