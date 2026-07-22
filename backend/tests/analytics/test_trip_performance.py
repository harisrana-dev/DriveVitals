"""Tests for TripPerformanceAnalyzer."""

from datetime import datetime

from analytics.analytics_input import AnalyticsInput
from analytics.trip_performance import TripPerformanceAnalyzer


def _make_input(**kwargs) -> AnalyticsInput:
    defaults = {
        "vehicle_id": "vehicle-001",
        "tick_id": 1,
        "timestamp": datetime(2026, 1, 1),
    }
    defaults.update(kwargs)
    return AnalyticsInput(**defaults)


def test_no_active_trip():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input()
    result = analyzer.analyze(ai, [])
    assert result["status"] == "not_initialized"
    assert result["reason"] == "no_active_trip"
    print("PASS: no_active_trip")


def test_active_trip():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input(
        trip_id="trip-001",
        driver_id="driver-001",
        distance_planned_km=50.0,
        distance_completed_km=2.5,
        duration_minutes=2.5,
        average_speed_kmh=60.0,
        fuel_consumed_liters=0.12,
        fuel_efficiency_km_per_liter=20.83,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "in_progress"
    assert result["trip_id"] == "trip-001"
    assert result["driver_id"] == "driver-001"
    assert result["distance_planned_km"] == 50.0
    assert result["distance_completed_km"] == 2.5
    assert result["progress_percent"] == 5.0
    assert result["distance_remaining_km"] == 47.5
    assert result["duration_minutes"] == 2.5
    assert result["average_speed_kmh"] == 60.0
    assert result["fuel_consumed_liters"] == 0.12
    assert result["fuel_efficiency_km_per_liter"] == 20.83
    print("PASS: active_trip")


def test_progress_calculation():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input(
        trip_id="trip-002",
        distance_planned_km=100.0,
        distance_completed_km=33.33,
    )
    result = analyzer.analyze(ai, [])
    assert result["progress_percent"] == 33.33
    assert result["distance_remaining_km"] == 66.67
    print("PASS: progress_calculation")


def test_zero_planned_distance():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input(
        trip_id="trip-003",
        distance_planned_km=0.0,
        distance_completed_km=5.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["progress_percent"] == 0.0
    assert result["distance_remaining_km"] == 0.0
    print("PASS: zero_planned_distance")


def test_trip_identity_propagated():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input(
        trip_id="trip-007",
        driver_id="driver-003",
        distance_planned_km=25.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["trip_id"] == "trip-007"
    assert result["driver_id"] == "driver-003"
    print("PASS: trip_identity_propagated")


def test_none_values_handled():
    analyzer = TripPerformanceAnalyzer()
    ai = _make_input(
        trip_id="trip-004",
        distance_planned_km=None,
        distance_completed_km=None,
        duration_minutes=None,
        average_speed_kmh=None,
        fuel_consumed_liters=None,
        fuel_efficiency_km_per_liter=None,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "in_progress"
    assert result["progress_percent"] == 0.0
    assert result["distance_remaining_km"] == 0.0
    print("PASS: none_values_handled")


if __name__ == "__main__":
    test_no_active_trip()
    test_active_trip()
    test_progress_calculation()
    test_zero_planned_distance()
    test_trip_identity_propagated()
    test_none_values_handled()
    print("\nALL TripPerformance TESTS PASSED")
