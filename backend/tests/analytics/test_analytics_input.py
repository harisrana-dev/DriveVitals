"""Tests for AnalyticsInput adapter."""

from datetime import datetime

from digital_twin.sensors.sensor_models import NumericSensorReading
from digital_twin.sensors.pid_mapper import PidMetadata
from digital_twin.telemetry.telemetry_packet import TelemetryPacket

from analytics.analytics_input import AnalyticsInput


def _make_reading(name: str, value: float, unit: str = "unit") -> NumericSensorReading:
    return NumericSensorReading(
        sensor_name=name,
        timestamp=datetime(2026, 1, 1),
        unit=unit,
        pid=PidMetadata(pid_code="0x00", mode="01", pid_name=name, is_standard=False),
        valid=True,
        value=value,
    )


def _make_packet(*readings: NumericSensorReading) -> TelemetryPacket:
    return TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 1, 1),
        sequence_number=0,
        sensor_readings=tuple(readings),
    )


def test_all_sensors_present():
    packet = _make_packet(
        _make_reading("vehicle_speed", 90.0, "km/h"),
        _make_reading("engine_rpm", 2500.0, "rpm"),
        _make_reading("gear_position", 3.0, "gear"),
        _make_reading("fuel_level", 85.5, "%"),
        _make_reading("engine_load", 45.0, "%"),
        _make_reading("engine_temperature", 88.0, "degC"),
        _make_reading("battery_voltage", 12.6, "V"),
        _make_reading("odometer", 15000.0, "km"),
        _make_reading("brake_pad_health", 75.0, "%"),
        _make_reading("tyre_health", 90.0, "%"),
    )

    ai = AnalyticsInput.from_packet(packet)

    assert ai.vehicle_id == "vehicle-001"
    assert ai.tick_id == 1
    assert ai.speed_kmh == 90.0
    assert ai.rpm == 2500.0
    assert ai.gear == 3.0
    assert ai.fuel_level_percent == 85.5
    assert ai.engine_load_percent == 45.0
    assert ai.engine_temperature_celsius == 88.0
    assert ai.battery_voltage == 12.6
    assert ai.odometer_km == 15000.0
    assert ai.brake_pad_health_percent == 75.0
    assert ai.tyre_health_percent == 90.0
    print("PASS: all_sensors_present")


def test_missing_sensors_are_none():
    packet = _make_packet(
        _make_reading("vehicle_speed", 60.0, "km/h"),
    )

    ai = AnalyticsInput.from_packet(packet)

    assert ai.speed_kmh == 60.0
    assert ai.rpm is None
    assert ai.gear is None
    assert ai.fuel_level_percent is None
    assert ai.engine_load_percent is None
    assert ai.engine_temperature_celsius is None
    assert ai.battery_voltage is None
    assert ai.odometer_km is None
    assert ai.brake_pad_health_percent is None
    assert ai.tyre_health_percent is None
    print("PASS: missing_sensors_are_none")


def test_empty_readings_raises():
    """TelemetryPacket itself prevents empty readings at construction."""
    from digital_twin.common.exceptions import ConfigurationError
    try:
        TelemetryPacket(
            vehicle_id="vehicle-001",
            tick_id=1,
            simulation_time=datetime(2026, 1, 1),
            sequence_number=0,
            sensor_readings=(),
        )
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError:
        pass
    print("PASS: empty_readings_raises (guarded by TelemetryPacket)")


def test_non_numeric_sensor_skipped():
    """A sensor reading that is not NumericSensorReading should be skipped."""
    from digital_twin.sensors.sensor_models import EnumeratedSensorReading

    reading = EnumeratedSensorReading(
        sensor_name="gear_position",
        timestamp=datetime(2026, 1, 1),
        unit="gear",
        pid=None,
        valid=True,
        value="DRIVE",
    )
    packet = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 1, 1),
        sequence_number=0,
        sensor_readings=(reading,),
    )

    ai = AnalyticsInput.from_packet(packet)
    assert ai.gear is None
    print("PASS: non_numeric_sensor_skipped")


def test_invalid_reading_skipped():
    """A reading with valid=False should be skipped."""
    reading = NumericSensorReading(
        sensor_name="vehicle_speed",
        timestamp=datetime(2026, 1, 1),
        unit="km/h",
        pid=None,
        valid=False,
        value=999.0,
    )
    packet = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 1, 1),
        sequence_number=0,
        sensor_readings=(reading,),
    )

    ai = AnalyticsInput.from_packet(packet)
    assert ai.speed_kmh is None
    print("PASS: invalid_reading_skipped")


def test_duplicate_sensor_first_wins():
    r1 = _make_reading("vehicle_speed", 80.0, "km/h")
    r2 = _make_reading("vehicle_speed", 120.0, "km/h")
    packet = _make_packet(r1, r2)

    ai = AnalyticsInput.from_packet(packet)
    assert ai.speed_kmh == 80.0
    print("PASS: duplicate_sensor_first_wins")


def test_unknown_sensor_ignored():
    r1 = _make_reading("vehicle_speed", 50.0, "km/h")
    r2 = _make_reading("unknown_sensor", 42.0, "x")
    packet = _make_packet(r1, r2)

    ai = AnalyticsInput.from_packet(packet)
    assert ai.speed_kmh == 50.0
    # No crash, unknown sensor simply ignored
    print("PASS: unknown_sensor_ignored")


def test_frozen_immutable():
    packet = _make_packet(_make_reading("vehicle_speed", 50.0))
    ai = AnalyticsInput.from_packet(packet)
    try:
        ai.speed_kmh = 999.0  # type: ignore
        assert False, "Should have raised"
    except AttributeError:
        pass
    print("PASS: frozen_immutable")


if __name__ == "__main__":
    test_all_sensors_present()
    test_missing_sensors_are_none()
    test_empty_readings_raises()
    test_non_numeric_sensor_skipped()
    test_invalid_reading_skipped()
    test_duplicate_sensor_first_wins()
    test_unknown_sensor_ignored()
    test_frozen_immutable()
    print("\nALL AnalyticsInput TESTS PASSED")
