"""Tests for FuelEfficiencyAnalyzer."""

from datetime import datetime

from analytics.analytics_input import AnalyticsInput
from analytics.fuel_efficiency import FuelEfficiencyAnalyzer


def _make_input(**kwargs) -> AnalyticsInput:
    defaults = {
        "vehicle_id": "vehicle-001",
        "tick_id": 1,
        "timestamp": datetime(2026, 1, 1),
    }
    defaults.update(kwargs)
    return AnalyticsInput(**defaults)


def test_unavailable_when_no_physics():
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(fuel_level_percent=75.0, speed_kmh=60.0)
    result = analyzer.analyze(ai, [])
    assert result["status"] == "unavailable"
    assert result["reason"] == "physics_tick_result_not_available"
    assert result["fuel_level_percent"] == 75.0
    print("PASS: unavailable_when_no_physics")


def test_zero_fuel_consumption():
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(
        distance_travelled_km=0.001,
        fuel_consumed_liters=0.0,
        fuel_level_percent=80.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "ok"
    assert result["mode"] == "idle"
    assert result["km_per_liter"] is None
    assert result["rating"] == "idle"
    print("PASS: zero_fuel_consumption")


def test_zero_distance_with_fuel():
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(
        distance_travelled_km=0.0,
        fuel_consumed_liters=0.001,
        fuel_level_percent=80.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "ok"
    assert result["mode"] == "stationary"
    assert result["km_per_liter"] == 0.0
    assert result["rating"] == "poor"
    print("PASS: zero_distance_with_fuel")


def test_normal_calculation():
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(
        distance_travelled_km=0.015,
        fuel_consumed_liters=0.001,
        fuel_level_percent=80.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "ok"
    assert result["mode"] == "driving"
    assert result["km_per_liter"] == 15.0
    assert result["rating"] == "excellent"
    print("PASS: normal_calculation")


def test_rating_thresholds():
    analyzer = FuelEfficiencyAnalyzer()

    # excellent (>=15)
    ai = _make_input(distance_travelled_km=0.03, fuel_consumed_liters=0.001)
    r = analyzer.analyze(ai, [])
    assert r["rating"] == "excellent"

    # good (>=10, <15)
    ai = _make_input(distance_travelled_km=0.012, fuel_consumed_liters=0.001)
    r = analyzer.analyze(ai, [])
    assert r["rating"] == "good"

    # average (>=5, <10)
    ai = _make_input(distance_travelled_km=0.007, fuel_consumed_liters=0.001)
    r = analyzer.analyze(ai, [])
    assert r["rating"] == "average"

    # poor (<5)
    ai = _make_input(distance_travelled_km=0.003, fuel_consumed_liters=0.001)
    r = analyzer.analyze(ai, [])
    assert r["rating"] == "poor"

    print("PASS: rating_thresholds")


def test_no_fabricated_fuel_rate():
    """Ensure no fuel_rate_lph field is ever returned."""
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(distance_travelled_km=0.01, fuel_consumed_liters=0.001)
    result = analyzer.analyze(ai, [])
    assert "fuel_rate_lph" not in result
    print("PASS: no_fabricated_fuel_rate")


def test_none_physics_fields():
    analyzer = FuelEfficiencyAnalyzer()
    ai = _make_input(distance_travelled_km=None, fuel_consumed_liters=None)
    result = analyzer.analyze(ai, [])
    assert result["status"] == "unavailable"
    print("PASS: none_physics_fields")


if __name__ == "__main__":
    test_unavailable_when_no_physics()
    test_zero_fuel_consumption()
    test_zero_distance_with_fuel()
    test_normal_calculation()
    test_rating_thresholds()
    test_no_fabricated_fuel_rate()
    test_none_physics_fields()
    print("\nALL FuelEfficiency TESTS PASSED")
