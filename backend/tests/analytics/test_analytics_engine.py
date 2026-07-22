"""Integration test: Digital Twin TelemetryPacket -> AnalyticsEngine."""

from dataclasses import dataclass
from datetime import datetime

from digital_twin.sensors.sensor_models import NumericSensorReading
from digital_twin.sensors.pid_mapper import PidMetadata
from digital_twin.telemetry.telemetry_packet import TelemetryPacket

from analytics.engine import AnalyticsEngine


def _make_reading(name: str, value: float, unit: str = "unit") -> NumericSensorReading:
    return NumericSensorReading(
        sensor_name=name,
        timestamp=datetime(2026, 1, 1),
        unit=unit,
        pid=PidMetadata(pid_code="0x00", mode="01", pid_name=name, is_standard=False),
        valid=True,
        value=value,
    )


@dataclass(frozen=True)
class _FakePhysicsResult:
    distance_travelled_km: float = 0.0
    fuel_consumed_liters: float = 0.0


@dataclass(frozen=True)
class _FakeTrip:
    trip_id: str = "trip-001"
    driver_id: str | None = "driver-001"
    vehicle_id: str | None = "vehicle-001"
    distance_planned_km: float = 50.0
    distance_completed_km: float = 0.0
    duration_minutes: float = 0.0
    average_speed_kmh: float = 0.0
    fuel_consumed_liters: float = 0.0
    fuel_efficiency_km_per_liter: float = 0.0


def test_full_pipeline_normal():
    """Process a normal telemetry packet through the full analytics pipeline."""
    engine = AnalyticsEngine()

    packet = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 7, 21, 12, 0, 0),
        sequence_number=0,
        sensor_readings=(
            _make_reading("vehicle_speed", 60.0, "km/h"),
            _make_reading("engine_rpm", 2000.0, "rpm"),
            _make_reading("gear_position", 3.0, "gear"),
            _make_reading("fuel_level", 85.0, "%"),
            _make_reading("engine_load", 45.0, "%"),
            _make_reading("engine_temperature", 85.0, "degC"),
            _make_reading("battery_voltage", 12.6, "V"),
            _make_reading("odometer", 15000.0, "km"),
            _make_reading("brake_pad_health", 80.0, "%"),
            _make_reading("tyre_health", 90.0, "%"),
        ),
    )

    result = engine.process(packet)

    assert result["vehicle_id"] == "vehicle-001"
    assert result["tick_id"] == 1
    assert result["events"] == []
    assert result["driver_behaviour"]["behaviour"] == "normal"
    assert result["vehicle_health"]["health"] == "healthy"
    assert result["fuel_efficiency"]["status"] == "unavailable"
    assert result["trip_performance"]["status"] == "not_initialized"
    assert result["driver_ranking"]["score"] == 100
    assert result["maintenance_queue"] == []
    assert isinstance(result["fleet_trends"], list)
    print("PASS: full_pipeline_normal")


def test_full_pipeline_overspeed():
    """Process an overspeeding vehicle."""
    engine = AnalyticsEngine()

    packet = TelemetryPacket(
        vehicle_id="vehicle-002",
        tick_id=5,
        simulation_time=datetime(2026, 7, 21, 12, 0, 4),
        sequence_number=4,
        sensor_readings=(
            _make_reading("vehicle_speed", 135.0, "km/h"),
            _make_reading("engine_rpm", 3000.0, "rpm"),
            _make_reading("fuel_level", 60.0, "%"),
            _make_reading("engine_temperature", 88.0, "degC"),
            _make_reading("battery_voltage", 12.4, "V"),
        ),
    )

    result = engine.process(packet)

    assert len(result["events"]) == 1
    assert result["events"][0]["event_type"] == "overspeed"
    assert result["driver_behaviour"]["indicators"] == ["overspeed_detected"]
    print("PASS: full_pipeline_overspeed")


def test_full_pipeline_critical_vehicle():
    """Process a vehicle with critical health conditions."""
    engine = AnalyticsEngine()

    packet = TelemetryPacket(
        vehicle_id="vehicle-003",
        tick_id=10,
        simulation_time=datetime(2026, 7, 21, 12, 0, 9),
        sequence_number=9,
        sensor_readings=(
            _make_reading("vehicle_speed", 20.0, "km/h"),
            _make_reading("engine_rpm", 5200.0, "rpm"),
            _make_reading("fuel_level", 10.0, "%"),
            _make_reading("engine_load", 90.0, "%"),
            _make_reading("engine_temperature", 112.0, "degC"),
            _make_reading("battery_voltage", 11.0, "V"),
            _make_reading("brake_pad_health", 25.0, "%"),
            _make_reading("tyre_health", 30.0, "%"),
        ),
    )

    result = engine.process(packet)

    assert len(result["events"]) == 5  # high_rpm, high_load, high_temp, low_fuel, low_battery
    assert result["vehicle_health"]["health"] == "critical"
    assert len(result["maintenance_queue"]) > 0
    print("PASS: full_pipeline_critical_vehicle")


def test_fleet_trends_accumulate():
    """Fleet trends should accumulate across multiple ticks."""
    engine = AnalyticsEngine()

    for tick in range(3):
        packet = TelemetryPacket(
            vehicle_id="vehicle-001",
            tick_id=tick,
            simulation_time=datetime(2026, 7, 21, 12, 0, tick),
            sequence_number=tick,
            sensor_readings=(
                _make_reading("vehicle_speed", 60.0 + tick * 10, "km/h"),
                _make_reading("engine_temperature", 85.0 + tick * 2, "degC"),
            ),
        )
        result = engine.process(packet)

    assert len(result["fleet_trends"]) == 3
    print("PASS: fleet_trends_accumulate")


def test_driver_ranking_dedup():
    """Same violation type should not deduct penalty twice for same vehicle."""
    engine = AnalyticsEngine()

    for tick in range(3):
        packet = TelemetryPacket(
            vehicle_id="vehicle-001",
            tick_id=tick,
            simulation_time=datetime(2026, 7, 21, 12, 0, tick),
            sequence_number=tick,
            sensor_readings=(
                _make_reading("vehicle_speed", 130.0, "km/h"),
            ),
        )
        result = engine.process(packet)

    # After 3 ticks of overspeed, score should be 100 - 15 = 85 (not 100 - 45)
    assert result["driver_ranking"]["score"] == 85
    print("PASS: driver_ranking_dedup")


def test_fuel_efficiency_with_physics():
    """Fuel efficiency calculated from real physics data."""
    engine = AnalyticsEngine()

    packet = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 7, 21, 12, 0, 0),
        sequence_number=0,
        sensor_readings=(
            _make_reading("vehicle_speed", 80.0, "km/h"),
            _make_reading("fuel_level", 90.0, "%"),
        ),
    )
    physics = _FakePhysicsResult(distance_travelled_km=0.015, fuel_consumed_liters=0.001)

    result = engine.process(packet, physics_result=physics)

    assert result["fuel_efficiency"]["status"] == "ok"
    assert result["fuel_efficiency"]["mode"] == "driving"
    assert result["fuel_efficiency"]["km_per_liter"] == 15.0
    assert result["fuel_efficiency"]["rating"] == "excellent"
    print("PASS: fuel_efficiency_with_physics")


def test_trip_performance_with_trip():
    """Trip performance from real trip domain data."""
    engine = AnalyticsEngine()

    packet = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=10,
        simulation_time=datetime(2026, 7, 21, 12, 0, 10),
        sequence_number=10,
        sensor_readings=(
            _make_reading("vehicle_speed", 60.0, "km/h"),
        ),
    )
    trip = _FakeTrip(
        distance_planned_km=50.0,
        distance_completed_km=2.5,
        duration_minutes=2.5,
        average_speed_kmh=60.0,
        fuel_consumed_liters=0.12,
        fuel_efficiency_km_per_liter=20.83,
    )

    result = engine.process(packet, trip=trip)

    tp = result["trip_performance"]
    assert tp["status"] == "in_progress"
    assert tp["trip_id"] == "trip-001"
    assert tp["distance_planned_km"] == 50.0
    assert tp["distance_completed_km"] == 2.5
    assert tp["progress_percent"] == 5.0
    assert tp["distance_remaining_km"] == 47.5
    assert tp["fuel_efficiency_km_per_liter"] == 20.83
    print("PASS: trip_performance_with_trip")


def test_event_lifecycle():
    """Events should become active and then resolve."""
    engine = AnalyticsEngine()

    # Tick 1: overspeed fires
    packet1 = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=1,
        simulation_time=datetime(2026, 7, 21, 12, 0, 0),
        sequence_number=0,
        sensor_readings=(_make_reading("vehicle_speed", 130.0, "km/h"),),
    )
    result1 = engine.process(packet1)
    assert len(result1["events"]) == 1
    assert result1["events"][0]["status"] == "ACTIVE"
    assert result1["events"][0]["occurrences"] == 1

    # Tick 2: overspeed still fires — occurrences should increment
    packet2 = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=2,
        simulation_time=datetime(2026, 7, 21, 12, 0, 1),
        sequence_number=1,
        sensor_readings=(_make_reading("vehicle_speed", 135.0, "km/h"),),
    )
    result2 = engine.process(packet2)
    assert len(result2["events"]) == 1
    assert result2["events"][0]["occurrences"] == 2
    assert result2["events"][0]["latest_value"] == 135.0

    # Tick 3: speed drops — event should resolve
    packet3 = TelemetryPacket(
        vehicle_id="vehicle-001",
        tick_id=3,
        simulation_time=datetime(2026, 7, 21, 12, 0, 2),
        sequence_number=2,
        sensor_readings=(_make_reading("vehicle_speed", 80.0, "km/h"),),
    )
    result3 = engine.process(packet3)
    assert len(result3["events"]) == 0  # no active events

    # Check resolved history
    resolved = engine.event_manager.get_resolved_events()
    assert len(resolved) == 1
    assert resolved[0].status == "RESOLVED"
    assert resolved[0].occurrences == 2
    assert resolved[0].event_type == "overspeed"
    print("PASS: event_lifecycle")


if __name__ == "__main__":
    test_full_pipeline_normal()
    test_full_pipeline_overspeed()
    test_full_pipeline_critical_vehicle()
    test_fleet_trends_accumulate()
    test_driver_ranking_dedup()
    test_fuel_efficiency_with_physics()
    test_trip_performance_with_trip()
    test_event_lifecycle()
    print("\nALL AnalyticsEngine INTEGRATION TESTS PASSED")
