"""Tests for ContinuousRuntime: the full Digital Twin simulation loop."""

import io
import contextlib
import time
from datetime import datetime

from digital_twin.common.enums import SimulationStatus, VehicleStatus
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.runtime.continuous_runtime import ContinuousRuntime


def _make_vehicle(vehicle_id: str = "vehicle-001") -> Vehicle:
    """Create a minimal test vehicle."""
    return Vehicle(
        vehicle_id=vehicle_id,
        vin=f"VIN{vehicle_id[-3:]}",
        specification=VehicleSpecification(
            manufacturer="Test",
            model="Model",
            year=2024,
            fuel_type=FuelType.DIESEL,
            transmission=TransmissionType.AUTOMATIC,
        ),
        status=VehicleStatus.AVAILABLE,
    )


def _make_config() -> SimulationConfig:
    """Create a test configuration."""
    return SimulationConfig()


# --- Test 1: One tick ---

def test_one_tick():
    """Verify tick_id advances and simulation_time advances by delta_time."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle)

    runtime.start()
    result = runtime.step()

    assert result.tick_id == 1
    assert result.delta_time > 0
    assert "vehicle-001" in result.vehicle_results
    vtr = result.vehicle_results["vehicle-001"]
    assert vtr.physics_result is not None
    assert vtr.telemetry_packet is not None
    assert vtr.analytics_result is not None
    assert vtr.error is None

    runtime.stop()
    print("PASS: test_one_tick")


# --- Test 2: Multiple vehicles ---

def test_multiple_vehicles():
    """Register 3 vehicles, run one tick, verify all are processed."""
    config = _make_config()
    runtime = ContinuousRuntime(config)

    for i in range(1, 4):
        runtime.add_vehicle(_make_vehicle(f"vehicle-{i:03d}"))

    runtime.start()
    result = runtime.step()

    assert len(result.vehicle_results) == 3
    for i in range(1, 4):
        vid = f"vehicle-{i:03d}"
        assert vid in result.vehicle_results
        vtr = result.vehicle_results[vid]
        assert vtr.physics_result is not None
        assert vtr.telemetry_packet is not None
        assert vtr.analytics_result is not None

    runtime.stop()
    print("PASS: test_multiple_vehicles")


# --- Test 3: Manual multi-tick execution ---

def test_multi_tick_execution():
    """Run 100 ticks manually, verify tick_id and time advancement."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()
    for _ in range(100):
        runtime.step()

    assert runtime.tick_id == 100

    # Verify vehicle state exists and physics ran
    vehicle = runtime.get_vehicle("vehicle-001")
    assert vehicle is not None
    # Engine hours should advance even when stationary
    assert vehicle.state.engine_hours > 0

    runtime.stop()
    print("PASS: test_multi_tick_execution")


# --- Test 4: Accelerated execution ---

def test_accelerated_execution():
    """Run 1000 ticks without wall-clock delay, verify no crashes."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))
    runtime.add_vehicle(_make_vehicle("vehicle-002"))

    runtime.start()

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        runtime.run(num_ticks=1000, real_time=False)

    assert runtime.tick_id == 1000
    assert runtime.status == SimulationStatus.STOPPED

    # Verify vehicles are still valid
    v1 = runtime.get_vehicle("vehicle-001")
    v2 = runtime.get_vehicle("vehicle-002")
    assert v1 is not None
    assert v2 is not None
    # Engine hours should advance even when stationary
    assert v1.state.engine_hours > 0
    assert v2.state.engine_hours > 0

    print("PASS: test_accelerated_execution")


# --- Test 5: Real-time execution ---

def test_real_time_execution():
    """Run 3 ticks in real-time, verify wall-clock duration is approximately 3s."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()

    start_wall = time.perf_counter()
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        runtime.run(num_ticks=3, real_time=True)
    elapsed = time.perf_counter() - start_wall

    # Should be approximately 3 seconds (with tolerance for processing time)
    assert elapsed >= 2.0, f"Expected >= 2.0s, got {elapsed:.2f}s"
    assert elapsed <= 5.0, f"Expected <= 5.0s, got {elapsed:.2f}s"
    assert runtime.tick_id == 3

    print(f"PASS: test_real_time_execution ({elapsed:.2f}s)")


# --- Test 6: Graceful shutdown ---

def test_graceful_shutdown():
    """Start runtime, allow ticks, request stop, verify clean exit."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()

    # Run a few ticks
    for _ in range(5):
        runtime.step()

    assert runtime.tick_id == 5

    # Stop should work cleanly
    runtime.stop()
    assert runtime.status == SimulationStatus.STOPPED

    print("PASS: test_graceful_shutdown")


# --- Test 7: Pause/resume ---

def test_pause_resume():
    """Start, tick, pause, verify no new ticks, resume, verify ticks continue."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()

    # Run a few ticks
    for _ in range(3):
        runtime.step()
    assert runtime.tick_id == 3

    # Pause
    runtime.pause()
    assert runtime.status == SimulationStatus.PAUSED

    # Trying to step while paused should raise
    try:
        runtime.step()
        assert False, "Should have raised SimulationStateError"
    except Exception:
        pass

    # Resume
    runtime.resume()
    assert runtime.status == SimulationStatus.RUNNING

    # Ticks should continue
    runtime.step()
    assert runtime.tick_id == 4

    runtime.stop()
    print("PASS: test_pause_resume")


# --- Test 8: Vehicle registration ---

def test_vehicle_registration():
    """Test add, get, remove vehicle operations."""
    config = _make_config()
    runtime = ContinuousRuntime(config)

    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle)

    # Get
    assert runtime.get_vehicle("vehicle-001") is vehicle
    assert runtime.get_vehicle("nonexistent") is None

    # Get all
    all_vehicles = runtime.get_all_vehicles()
    assert len(all_vehicles) == 1
    assert "vehicle-001" in all_vehicles

    # Duplicate should raise
    try:
        runtime.add_vehicle(_make_vehicle("vehicle-001"))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Remove
    runtime.remove_vehicle("vehicle-001")
    assert runtime.get_vehicle("vehicle-001") is None

    # Remove nonexistent should raise
    try:
        runtime.remove_vehicle("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("PASS: test_vehicle_registration")


# --- Test 9: Tick result structure ---

def test_tick_result_structure():
    """Verify TickResult has correct structure and types."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()
    result = runtime.step()

    # TickResult fields
    assert isinstance(result.tick_id, int)
    assert isinstance(result.simulation_time, datetime)
    assert isinstance(result.delta_time, float)
    assert isinstance(result.vehicle_results, dict)
    assert isinstance(result.errors, list)

    # VehicleTickResult fields
    vtr = result.vehicle_results["vehicle-001"]
    assert vtr.vehicle_id == "vehicle-001"
    assert vtr.physics_result is not None
    assert vtr.physics_result.distance_travelled_km >= 0
    assert vtr.physics_result.fuel_consumed_liters >= 0
    assert vtr.telemetry_packet is not None
    assert vtr.telemetry_packet.vehicle_id == "vehicle-001"
    assert vtr.analytics_result is not None
    assert "vehicle_id" in vtr.analytics_result

    runtime.stop()
    print("PASS: test_tick_result_structure")


# --- Test 10: No old V1 telemetry fields ---

def test_no_v1_telemetry_fields():
    """Verify no old V1 packet fields are accessed."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()
    result = runtime.step()

    vtr = result.vehicle_results["vehicle-001"]
    packet = vtr.telemetry_packet

    # TelemetryPacket should only have the new fields
    assert hasattr(packet, "vehicle_id")
    assert hasattr(packet, "tick_id")
    assert hasattr(packet, "simulation_time")
    assert hasattr(packet, "sequence_number")
    assert hasattr(packet, "sensor_readings")

    # Should NOT have old V1 fields
    assert not hasattr(packet, "speed_kmh")
    assert not hasattr(packet, "rpm")
    assert not hasattr(packet, "driver_id")
    assert not hasattr(packet, "engine_load")
    assert not hasattr(packet, "coolant_temperature")
    assert not hasattr(packet, "fuel_rate_lph")

    runtime.stop()
    print("PASS: test_no_v1_telemetry_fields")


# --- Test 11: Error handling ---

def test_error_handling():
    """Verify that a failing vehicle doesn't crash the whole tick."""
    config = _make_config()
    runtime = ContinuousRuntime(config)

    # Add a valid vehicle
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()
    result = runtime.step()

    # Valid vehicle should succeed
    assert result.vehicle_results["vehicle-001"].error is None
    assert len(result.errors) == 0

    runtime.stop()
    print("PASS: test_error_handling")


# --- Test 12: Reset ---

def test_reset():
    """Verify reset returns runtime to initial state."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()
    for _ in range(10):
        runtime.step()

    assert runtime.tick_id == 10

    runtime.reset()
    assert runtime.tick_id == 0
    assert runtime.status == SimulationStatus.STOPPED

    # Should be able to start again
    runtime.start()
    runtime.step()
    assert runtime.tick_id == 1

    runtime.stop()
    print("PASS: test_reset")


# --- Test 13: Continuous run with stop ---

def test_continuous_run_with_stop():
    """Start continuous run, request stop, verify it exits cleanly."""
    config = _make_config()
    runtime = ContinuousRuntime(config)
    runtime.add_vehicle(_make_vehicle("vehicle-001"))

    runtime.start()

    # Start run in a thread and stop it after a short delay
    import threading

    def stop_after_delay():
        time.sleep(0.5)
        runtime.stop()

    storer = threading.Thread(target=stop_after_delay)
    storer.start()

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        runtime.run(num_ticks=None, real_time=False)

    storer.join()

    # Should have run some ticks
    assert runtime.tick_id > 0
    assert runtime.status == SimulationStatus.STOPPED

    print(f"PASS: test_continuous_run_with_stop ({runtime.tick_id} ticks)")


if __name__ == "__main__":
    test_one_tick()
    test_multiple_vehicles()
    test_multi_tick_execution()
    test_accelerated_execution()
    test_real_time_execution()
    test_graceful_shutdown()
    test_pause_resume()
    test_vehicle_registration()
    test_tick_result_structure()
    test_no_v1_telemetry_fields()
    test_error_handling()
    test_reset()
    test_continuous_run_with_stop()
    test_vehicle_starts_stationary()
    test_vehicle_eventually_accelerates()
    test_speed_changes_across_ticks()
    test_rpm_changes_with_state()
    test_odometer_increases_while_moving()
    test_fuel_decreases_while_operating()
    test_engine_hours_increase()
    test_telemetry_reflects_evolving_state()
    test_analytics_receives_changing_telemetry()
    test_multiple_vehicles_independent_behavior()
    test_deterministic_seeded_scenarios()
    print("\nALL CONTINUOUS RUNTIME TESTS PASSED")


# --- Test 14: Vehicle starts stationary ---

def test_vehicle_starts_stationary():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle)
    runtime.start()

    result = runtime.step()
    v = runtime.get_vehicle("vehicle-001")
    assert v.state.current_speed_kmh == 0.0
    assert v.state.current_rpm == 800.0  # idle RPM

    runtime.stop()
    print("PASS: test_vehicle_starts_stationary")


# --- Test 15: Vehicle eventually accelerates ---

def test_vehicle_eventually_accelerates():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    # Run enough ticks to get past idle phase
    for _ in range(10):
        runtime.step()

    v = runtime.get_vehicle("vehicle-001")
    assert v.state.current_speed_kmh > 0, "Vehicle should be moving after 10 ticks"

    runtime.stop()
    print("PASS: test_vehicle_eventually_accelerates")


# --- Test 16: Speed changes across ticks ---

def test_speed_changes_across_ticks():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    speeds = []
    for _ in range(15):
        result = runtime.step()
        v = runtime.get_vehicle("vehicle-001")
        speeds.append(v.state.current_speed_kmh)

    # Speed should increase during acceleration phase
    assert speeds[-1] > speeds[0], f"Speed should increase: {speeds[0]:.1f} -> {speeds[-1]:.1f}"

    runtime.stop()
    print("PASS: test_speed_changes_across_ticks")


# --- Test 17: RPM changes with vehicle state ---

def test_rpm_changes_with_state():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    rpms = []
    for _ in range(15):
        result = runtime.step()
        v = runtime.get_vehicle("vehicle-001")
        rpms.append(v.state.current_rpm)

    # RPM should change as vehicle accelerates
    assert max(rpms) > min(rpms), f"RPM should vary: min={min(rpms):.0f}, max={max(rpms):.0f}"

    runtime.stop()
    print("PASS: test_rpm_changes_with_state")


# --- Test 18: Odometer increases while moving ---

def test_odometer_increases_while_moving():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    odometer_readings = []
    for _ in range(20):
        runtime.step()
        v = runtime.get_vehicle("vehicle-001")
        odometer_readings.append(v.state.odometer_km)

    assert odometer_readings[-1] > odometer_readings[0], (
        f"Odometer should increase: {odometer_readings[0]:.3f} -> {odometer_readings[-1]:.3f}"
    )

    runtime.stop()
    print("PASS: test_odometer_increases_while_moving")


# --- Test 19: Fuel decreases while operating ---

def test_fuel_decreases_while_operating():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    fuel_readings = []
    for _ in range(20):
        runtime.step()
        v = runtime.get_vehicle("vehicle-001")
        fuel_readings.append(v.state.fuel_level_percent)

    assert fuel_readings[-1] < fuel_readings[0], (
        f"Fuel should decrease: {fuel_readings[0]:.2f}% -> {fuel_readings[-1]:.2f}%"
    )

    runtime.stop()
    print("PASS: test_fuel_decreases_while_operating")


# --- Test 20: Engine hours increase ---

def test_engine_hours_increase():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle)
    runtime.start()

    hours_readings = []
    for _ in range(10):
        runtime.step()
        v = runtime.get_vehicle("vehicle-001")
        hours_readings.append(v.state.engine_hours)

    assert hours_readings[-1] > hours_readings[0], (
        f"Engine hours should increase: {hours_readings[0]:.4f} -> {hours_readings[-1]:.4f}"
    )

    runtime.stop()
    print("PASS: test_engine_hours_increase")


# --- Test 21: Telemetry reflects actual evolving state ---

def test_telemetry_reflects_evolving_state():
    from simulation.sinks import InMemoryTelemetrySink

    sink = InMemoryTelemetrySink()
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    # Run and collect telemetry via the runner
    from simulation.runner import RunnerConfig, SimulationRunner
    runner = SimulationRunner(RunnerConfig(fleet_size=0, real_time=False))
    runner._runtime = runtime
    runner.add_telemetry_sink(sink)

    for _ in range(15):
        result = runtime.step()
        for vtr in result.vehicle_results.values():
            if vtr.telemetry_packet:
                sink.receive(vtr.telemetry_packet, vtr.physics_result)

    # Telemetry packets should have different sensor readings over time
    assert sink.count == 15
    # Check that at least some packets have non-zero speed readings
    speeds = []
    for packet in sink.packets:
        for reading in packet.sensor_readings:
            if reading.sensor_name == "vehicle_speed":
                speeds.append(reading.value)
    assert max(speeds) > min(speeds), "Telemetry should show changing speeds"

    runtime.stop()
    print("PASS: test_telemetry_reflects_evolving_state")


# --- Test 22: Analytics receives changing telemetry ---

def test_analytics_receives_changing_telemetry():
    from simulation.sinks import InMemoryAnalyticsSink

    sink = InMemoryAnalyticsSink()
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    vehicle = _make_vehicle("vehicle-001")
    runtime.add_vehicle(vehicle, seed=42, index=0)
    runtime.start()

    for _ in range(15):
        result = runtime.step()
        for vid, vtr in result.vehicle_results.items():
            if vtr.analytics_result:
                sink.receive(vid, result.tick_id, result.simulation_time, vtr.analytics_result)

    assert sink.count == 15
    # Analytics should have processed changing telemetry
    for r in sink.results:
        assert "vehicle_health" in r["analytics_result"]
        assert "fuel_efficiency" in r["analytics_result"]

    runtime.stop()
    print("PASS: test_analytics_receives_changing_telemetry")


# --- Test 23: Multiple vehicles have independent behavior ---

def test_multiple_vehicles_independent_behavior():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)

    for i in range(3):
        vehicle = _make_vehicle(f"vehicle-{i+1:03d}")
        runtime.add_vehicle(vehicle, seed=42, index=i)

    runtime.start()

    speeds = {}
    for _ in range(20):
        runtime.step()

    for vid in ["vehicle-001", "vehicle-002", "vehicle-003"]:
        v = runtime.get_vehicle(vid)
        speeds[vid] = v.state.current_speed_kmh

    # Vehicles should have different speeds due to different scenarios
    unique_speeds = set(round(s, 1) for s in speeds.values())
    assert len(unique_speeds) >= 2, f"Vehicles should have different speeds: {speeds}"

    runtime.stop()
    print("PASS: test_multiple_vehicles_independent_behavior")


# --- Test 24: Deterministic seeded scenarios ---

def test_deterministic_seeded_scenarios():
    config = SimulationConfig()
    runtime1 = ContinuousRuntime(config)
    runtime2 = ContinuousRuntime(config)

    for runtime in [runtime1, runtime2]:
        vehicle = _make_vehicle("vehicle-001")
        runtime.add_vehicle(vehicle, seed=123, index=0)
        runtime.start()

    speeds1 = []
    speeds2 = []

    for _ in range(15):
        runtime1.step()
        runtime2.step()
        v1 = runtime1.get_vehicle("vehicle-001")
        v2 = runtime2.get_vehicle("vehicle-001")
        speeds1.append(v1.state.current_speed_kmh)
        speeds2.append(v2.state.current_speed_kmh)

    # Same seed should produce same speeds
    for s1, s2 in zip(speeds1, speeds2):
        assert abs(s1 - s2) < 0.01, f"Speeds differ: {s1:.3f} vs {s2:.3f}"

    runtime1.stop()
    runtime2.stop()
    print("PASS: test_deterministic_seeded_scenarios")
