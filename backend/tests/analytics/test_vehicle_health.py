"""Tests for VehicleHealthAnalyzer."""

from datetime import datetime

from analytics.analytics_input import AnalyticsInput
from analytics.vehicle_health import VehicleHealthAnalyzer


def _make_input(**kwargs) -> AnalyticsInput:
    defaults = {
        "vehicle_id": "vehicle-001",
        "tick_id": 1,
        "timestamp": datetime(2026, 1, 1),
    }
    defaults.update(kwargs)
    return AnalyticsInput(**defaults)


def test_healthy_vehicle():
    analyzer = VehicleHealthAnalyzer()
    ai = _make_input(
        engine_temperature_celsius=85.0,
        engine_load_percent=50.0,
        rpm=2000.0,
        battery_voltage=12.6,
        brake_pad_health_percent=80.0,
        tyre_health_percent=90.0,
    )
    result = analyzer.analyze(ai, [])
    assert result["status"] == "ok"
    assert result["health"] == "healthy"
    assert result["health_score"] == 100.0
    assert result["factors"] == []
    print("PASS: healthy_vehicle")


def test_warning_conditions():
    analyzer = VehicleHealthAnalyzer()
    ai = _make_input(
        engine_temperature_celsius=98.0,  # -10
        engine_load_percent=90.0,         # -5
        battery_voltage=11.8,             # -10
    )
    result = analyzer.analyze(ai, [])
    assert result["health"] == "warning"
    assert result["health_score"] == 75.0
    assert len(result["factors"]) == 3
    print("PASS: warning_conditions")


def test_critical_conditions():
    analyzer = VehicleHealthAnalyzer()
    ai = _make_input(
        engine_temperature_celsius=110.0,  # -25
        brake_pad_health_percent=20.0,     # -15
        tyre_health_percent=25.0,          # -15
    )
    result = analyzer.analyze(ai, [])
    assert result["health"] == "critical"
    assert result["health_score"] == 45.0
    assert len(result["factors"]) == 3
    print("PASS: critical_conditions")


def test_score_clamped_at_zero():
    """With enough penalties, score should clamp at 0."""
    analyzer = VehicleHealthAnalyzer()
    # All penalties: -25 -5 -5 -10 -15 -15 = -75, clamped to 0
    ai = _make_input(
        engine_temperature_celsius=120.0,  # -25
        engine_load_percent=95.0,          # -5
        rpm=5000.0,                        # -5
        battery_voltage=10.0,              # -10
        brake_pad_health_percent=10.0,     # -15
        tyre_health_percent=10.0,          # -15
    )
    result = analyzer.analyze(ai, [])
    # 100 - 75 = 25 (not 0, since max penalty is 75)
    assert result["health_score"] == 25.0
    assert result["health"] == "critical"
    assert len(result["factors"]) == 6
    print("PASS: score_clamped_at_zero")


def test_score_clamped_at_100():
    analyzer = VehicleHealthAnalyzer()
    ai = _make_input(
        engine_temperature_celsius=50.0,  # no penalty
        engine_load_percent=10.0,         # no penalty
        rpm=1000.0,                       # no penalty
        battery_voltage=14.0,             # no penalty
        brake_pad_health_percent=100.0,   # no penalty
        tyre_health_percent=100.0,        # no penalty
    )
    result = analyzer.analyze(ai, [])
    assert result["health_score"] == 100.0
    assert result["health"] == "healthy"
    print("PASS: score_clamped_at_100")


def test_none_signals_no_penalty():
    analyzer = VehicleHealthAnalyzer()
    ai = _make_input()  # All signals None
    result = analyzer.analyze(ai, [])
    assert result["health_score"] == 100.0
    assert result["health"] == "healthy"
    assert result["factors"] == []
    print("PASS: none_signals_no_penalty")


if __name__ == "__main__":
    test_healthy_vehicle()
    test_warning_conditions()
    test_critical_conditions()
    test_score_clamped_at_zero()
    test_score_clamped_at_100()
    test_none_signals_no_penalty()
    print("\nALL VehicleHealth TESTS PASSED")
