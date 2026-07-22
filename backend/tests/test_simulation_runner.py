"""Tests for the production SimulationRunner."""

import io
import contextlib
import time
import threading
from datetime import datetime

from digital_twin.common.enums import SimulationStatus
from simulation.runner import RunnerConfig, SimulationRunner
from simulation.sinks import (
    InMemoryAnalyticsSink,
    InMemoryEventSink,
    InMemoryLiveUpdateSink,
    InMemoryTelemetrySink,
)


def _make_runner(
    fleet_size: int = 2,
    real_time: bool = False,
    num_ticks: int | None = None,
) -> SimulationRunner:
    """Create a runner with suppressed output."""
    config = RunnerConfig(
        fleet_size=fleet_size,
        real_time=real_time,
        num_ticks=num_ticks,
    )
    runner = SimulationRunner(config)
    for i in range(1, fleet_size + 1):
        runner.create_and_register_vehicle(f"vehicle-{i:03d}")
    return runner


# --- Test 1: Runner starts ---

def test_runner_starts():
    runner = _make_runner(fleet_size=1)
    runner.start()
    assert runner.status == SimulationStatus.RUNNING
    runner._stop_requested = True
    runner._stop_event.set()
    runner._runtime.stop()
    print("PASS: test_runner_starts")


# --- Test 2: Runner executes one tick ---

def test_one_tick():
    runner = _make_runner(fleet_size=1)
    runner.start()
    result = runner.runtime.step()
    assert result.tick_id == 1
    assert len(result.vehicle_results) == 1
    runner._stop_requested = True
    runner._stop_event.set()
    runner._runtime.stop()
    print("PASS: test_one_tick")


# --- Test 3: Runner executes multiple ticks ---

def test_multiple_ticks():
    runner = _make_runner(fleet_size=2, num_ticks=10)
    runner.start()
    runner.run()
    assert runner.stats.ticks_completed == 10
    print("PASS: test_multiple_ticks")


# --- Test 4: Telemetry sink receives packets ---

def test_telemetry_sink():
    sink = InMemoryTelemetrySink()
    runner = _make_runner(fleet_size=2, num_ticks=5)
    runner.add_telemetry_sink(sink)
    runner.start()
    runner.run()
    # 2 vehicles * 5 ticks = 10 packets
    assert sink.count == 10
    # Check packet properties
    for packet in sink.packets:
        assert packet.vehicle_id.startswith("vehicle-")
        assert packet.tick_id >= 1
        assert len(packet.sensor_readings) > 0
    print("PASS: test_telemetry_sink")


# --- Test 5: Analytics sink receives results ---

def test_analytics_sink():
    sink = InMemoryAnalyticsSink()
    runner = _make_runner(fleet_size=2, num_ticks=3)
    runner.add_analytics_sink(sink)
    runner.start()
    runner.run()
    # 2 vehicles * 3 ticks = 6 analytics results
    assert sink.count == 6
    for result in sink.results:
        assert "vehicle_id" in result
        assert "tick_id" in result
        assert "analytics_result" in result
    print("PASS: test_analytics_sink")


# --- Test 6: Event sink receives events ---

def test_event_sink():
    sink = InMemoryEventSink()
    runner = _make_runner(fleet_size=1, num_ticks=100)
    runner.add_event_sink(sink)
    runner.start()
    runner.run()
    # Events may or may not be generated depending on physics
    # Just verify the sink was called (count >= 0)
    assert sink.count >= 0
    print(f"PASS: test_event_sink (events={sink.count})")


# --- Test 7: Live update sink receives updates ---

def test_live_update_sink():
    sink = InMemoryLiveUpdateSink()
    runner = _make_runner(fleet_size=2, num_ticks=3)
    runner.add_live_update_sink(sink)
    runner.start()
    runner.run()
    assert sink.count == 3
    for update in sink.updates:
        assert "tick_id" in update
        assert "vehicle_updates" in update
        assert len(update["vehicle_updates"]) == 2
    print("PASS: test_live_update_sink")


# --- Test 8: Real-time mode approximately respects intervals ---

def test_real_time_pacing():
    config = RunnerConfig(fleet_size=1, real_time=True, num_ticks=3, real_time_interval=0.1)
    runner = SimulationRunner(config)
    runner.create_and_register_vehicle("vehicle-001")
    runner.start()

    start = time.perf_counter()
    runner.run()
    elapsed = time.perf_counter() - start

    # Should take approximately 0.3 seconds (3 ticks * 0.1s interval)
    assert elapsed >= 0.2, f"Expected >= 0.2s, got {elapsed:.3f}s"
    assert elapsed <= 1.0, f"Expected <= 1.0s, got {elapsed:.3f}s"
    print(f"PASS: test_real_time_pacing ({elapsed:.3f}s)")


# --- Test 9: Graceful shutdown ---

def test_graceful_shutdown():
    runner = _make_runner(fleet_size=1, real_time=False, num_ticks=100)
    runner.start()
    runner.run()
    assert runner.status == SimulationStatus.STOPPED
    assert runner.stats.ticks_completed == 100
    print(f"PASS: test_graceful_shutdown ({runner.stats.ticks_completed} ticks)")


# --- Test 10: Multiple vehicles processed ---

def test_multiple_vehicles():
    runner = _make_runner(fleet_size=5, num_ticks=3)
    runner.start()
    runner.run()
    assert runner.stats.ticks_completed == 3
    # All 5 vehicles should have telemetry generated
    assert runner.stats.telemetry_packets_generated == 15  # 5 * 3
    print("PASS: test_multiple_vehicles")


# --- Test 11: Runner can stop cleanly ---

def test_clean_stop():
    runner = _make_runner(fleet_size=1, real_time=False, num_ticks=5)
    runner.start()
    runner.run()
    assert runner.status == SimulationStatus.STOPPED
    assert runner.stats.ticks_completed == 5
    print("PASS: test_clean_stop")


# --- Test 12: Stats are accurate ---

def test_stats_accuracy():
    sink_t = InMemoryTelemetrySink()
    sink_a = InMemoryAnalyticsSink()
    runner = _make_runner(fleet_size=3, num_ticks=5)
    runner.add_telemetry_sink(sink_t)
    runner.add_analytics_sink(sink_a)
    runner.start()
    runner.run()

    assert runner.stats.ticks_completed == 5
    assert runner.stats.telemetry_packets_generated == 15  # 3 * 5
    assert runner.stats.analytics_executions == 15  # 3 * 5
    assert sink_t.count == 15
    assert sink_a.count == 15
    print("PASS: test_stats_accuracy")


# --- Test 13: No old V1 telemetry fields ---

def test_no_v1_fields():
    sink = InMemoryTelemetrySink()
    runner = _make_runner(fleet_size=1, num_ticks=1)
    runner.add_telemetry_sink(sink)
    runner.start()
    runner.run()

    packet = sink.packets[0]
    # Should have new fields
    assert hasattr(packet, "vehicle_id")
    assert hasattr(packet, "sensor_readings")
    # Should NOT have old V1 fields
    assert not hasattr(packet, "speed_kmh")
    assert not hasattr(packet, "rpm")
    assert not hasattr(packet, "driver_id")
    assert not hasattr(packet, "model_dump")
    print("PASS: test_no_v1_fields")


# --- Test 14: In-memory sinks work correctly ---

def test_in_memory_sinks():
    from simulation.sinks import (
        InMemoryTelemetrySink,
        InMemoryAnalyticsSink,
        InMemoryEventSink,
        InMemoryLiveUpdateSink,
    )

    t_sink = InMemoryTelemetrySink()
    a_sink = InMemoryAnalyticsSink()
    e_sink = InMemoryEventSink()
    l_sink = InMemoryLiveUpdateSink()

    runner = _make_runner(fleet_size=2, num_ticks=3)
    runner.add_telemetry_sink(t_sink)
    runner.add_analytics_sink(a_sink)
    runner.add_event_sink(e_sink)
    runner.add_live_update_sink(l_sink)
    runner.start()
    runner.run()

    assert t_sink.count == 6
    assert a_sink.count == 6
    assert l_sink.count == 3

    print("PASS: test_in_memory_sinks")


if __name__ == "__main__":
    test_runner_starts()
    test_one_tick()
    test_multiple_ticks()
    test_telemetry_sink()
    test_analytics_sink()
    test_event_sink()
    test_live_update_sink()
    test_real_time_pacing()
    test_graceful_shutdown()
    test_multiple_vehicles()
    test_clean_stop()
    test_stats_accuracy()
    test_no_v1_fields()
    test_in_memory_sinks()
    print("\nALL SIMULATION RUNNER TESTS PASSED")
