"""Tests for the RuleEngine with AnalyticsInput."""

from datetime import datetime

from analytics.analytics_input import AnalyticsInput
from analytics.rule_engine import RuleEngine


def _make_input(**kwargs) -> AnalyticsInput:
    defaults = {
        "vehicle_id": "vehicle-001",
        "tick_id": 1,
        "timestamp": datetime(2026, 1, 1),
    }
    defaults.update(kwargs)
    return AnalyticsInput(**defaults)


def test_normal_telemetry_no_events():
    engine = RuleEngine()
    ai = _make_input(
        speed_kmh=60.0,
        rpm=2000.0,
        engine_load_percent=50.0,
        engine_temperature_celsius=85.0,
        fuel_level_percent=75.0,
        battery_voltage=12.6,
    )
    events = engine.evaluate(ai)
    assert events == []
    print("PASS: normal_telemetry_no_events")


def test_overspeed():
    engine = RuleEngine()
    ai = _make_input(speed_kmh=130.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R001"
    assert events[0].event == "overspeed"
    assert events[0].value == 130.0
    assert events[0].severity == "WARNING"
    print("PASS: overspeed")


def test_high_rpm():
    engine = RuleEngine()
    ai = _make_input(rpm=5500.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R002"
    assert events[0].event == "high_rpm"
    print("PASS: high_rpm")


def test_high_engine_load():
    engine = RuleEngine()
    ai = _make_input(engine_load_percent=90.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R003"
    assert events[0].event == "high_engine_load"
    print("PASS: high_engine_load")


def test_high_engine_temperature():
    engine = RuleEngine()
    ai = _make_input(engine_temperature_celsius=110.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R004"
    assert events[0].event == "high_engine_temperature"
    assert events[0].severity == "CRITICAL"
    print("PASS: high_engine_temperature")


def test_low_fuel():
    engine = RuleEngine()
    ai = _make_input(fuel_level_percent=10.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R005"
    assert events[0].event == "low_fuel"
    print("PASS: low_fuel")


def test_low_battery():
    engine = RuleEngine()
    ai = _make_input(battery_voltage=11.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R006"
    assert events[0].event == "low_battery"
    print("PASS: low_battery")


def test_excessive_idle():
    engine = RuleEngine()
    ai = _make_input(speed_kmh=0.0, rpm=1500.0)
    events = engine.evaluate(ai)
    assert len(events) == 1
    assert events[0].rule_id == "DV-R007"
    assert events[0].event == "excessive_idle"
    assert events[0].severity == "INFO"
    print("PASS: excessive_idle")


def test_none_signals_skipped():
    """Rules should not fire when signals are None."""
    engine = RuleEngine()
    ai = _make_input()  # All signals are None
    events = engine.evaluate(ai)
    assert events == []
    print("PASS: none_signals_skipped")


def test_multiple_rules_firing():
    engine = RuleEngine()
    ai = _make_input(
        speed_kmh=130.0,
        rpm=5500.0,
        engine_temperature_celsius=110.0,
    )
    events = engine.evaluate(ai)
    assert len(events) == 3
    event_keys = {e.event for e in events}
    assert "overspeed" in event_keys
    assert "high_rpm" in event_keys
    assert "high_engine_temperature" in event_keys
    print("PASS: multiple_rules_firing")


def test_event_to_dict():
    engine = RuleEngine()
    ai = _make_input(speed_kmh=130.0)
    events = engine.evaluate(ai)
    d = events[0].to_dict()
    assert isinstance(d, dict)
    assert d["rule_id"] == "DV-R001"
    assert d["event"] == "overspeed"
    assert d["vehicle_id"] == "vehicle-001"
    print("PASS: event_to_dict")


if __name__ == "__main__":
    test_normal_telemetry_no_events()
    test_overspeed()
    test_high_rpm()
    test_high_engine_load()
    test_high_engine_temperature()
    test_low_fuel()
    test_low_battery()
    test_excessive_idle()
    test_none_signals_skipped()
    test_multiple_rules_firing()
    test_event_to_dict()
    print("\nALL RuleEngine TESTS PASSED")
