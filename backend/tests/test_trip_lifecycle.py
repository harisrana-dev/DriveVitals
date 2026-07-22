"""Integration tests for continuous trip lifecycle management.

Tests trip completion, new trip creation, and long-duration simulation
with multiple vehicles cycling through multiple trips.
"""

import io
import contextlib
from datetime import datetime

from digital_twin.common.enums import TripStatus
from digital_twin.simulation.simulation_runner import RunnerConfig, SimulationRunner
from digital_twin.entities.trip import Trip


def _make_runner(
    fleet_size: int = 1,
    num_ticks: int = 100,
    trip_distance_km: float = 50.0,
) -> SimulationRunner:
    """Create a runner with suppressed output and configurable trip distance."""
    config = RunnerConfig(
        fleet_size=fleet_size,
        num_ticks=num_ticks,
        real_time_pacing=False,
    )
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        runner = SimulationRunner(config=config)
        runner.start()
    # Set trip distance for testing (both current trip and future trips)
    for unit in runner._vehicle_units.values():
        unit.trip_distance_km = trip_distance_km
        unit.trip_entity.distance_planned_km = trip_distance_km
    return runner


def test_trip_completes_exactly_at_destination():
    """A trip should complete when distance_completed >= distance_planned."""
    runner = _make_runner(fleet_size=1, num_ticks=15, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(15):
            runner.run_tick()

    unit = runner._vehicle_units["vehicle-001"]

    # Should have completed at least one trip
    assert len(unit.completed_trips) >= 1, (
        f"Expected at least 1 completed trip, got {len(unit.completed_trips)}"
    )

    # The completed trip should have status COMPLETED
    completed = unit.completed_trips[0]
    assert completed.status == TripStatus.COMPLETED
    assert completed.distance_completed_km >= completed.distance_planned_km * 0.999
    assert completed.end_time is not None

    # Current trip should be a new one, IN_PROGRESS
    current = unit.trip_entity
    assert current.status == TripStatus.IN_PROGRESS
    assert current.trip_id != completed.trip_id
    assert current.distance_completed_km < current.distance_planned_km

    print("PASS: trip_completes_exactly_at_destination")


def test_progress_never_exceeds_100_percent():
    """No trip should ever report progress > 100%."""
    runner = _make_runner(fleet_size=2, num_ticks=50, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(50):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        for trip in unit.completed_trips:
            progress = (trip.distance_completed_km / trip.distance_planned_km) * 100
            assert progress <= 100.001, (
                f"{vehicle_id}/{trip.trip_id}: progress={progress:.2f}% > 100%"
            )

        current = unit.trip_entity
        progress = (current.distance_completed_km / current.distance_planned_km) * 100
        assert progress <= 100.001, (
            f"{vehicle_id}/current: progress={progress:.2f}% > 100%"
        )

    print("PASS: progress_never_exceeds_100_percent")


def test_remaining_distance_never_negative():
    """Remaining distance should never be negative."""
    runner = _make_runner(fleet_size=2, num_ticks=50, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(50):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        for trip in unit.completed_trips:
            remaining = trip.distance_planned_km - trip.distance_completed_km
            assert remaining >= -0.001, (
                f"{vehicle_id}/{trip.trip_id}: remaining={remaining:.4f} < 0"
            )

        current = unit.trip_entity
        remaining = current.distance_planned_km - current.distance_completed_km
        assert remaining >= -0.001, (
            f"{vehicle_id}/current: remaining={remaining:.4f} < 0"
        )

    print("PASS: remaining_distance_never_negative")


def test_completed_trips_have_correct_status():
    """No completed trip should remain in_progress."""
    runner = _make_runner(fleet_size=2, num_ticks=50, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(50):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        for trip in unit.completed_trips:
            assert trip.status == TripStatus.COMPLETED, (
                f"{vehicle_id}/{trip.trip_id}: status={trip.status} "
                f"expected COMPLETED"
            )

    print("PASS: completed_trips_have_correct_status")


def test_unique_trip_ids():
    """Every trip should have a unique trip ID."""
    runner = _make_runner(fleet_size=3, num_ticks=100, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(100):
            runner.run_tick()

    all_ids: list[str] = []
    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        for trip in unit.completed_trips:
            all_ids.append(trip.trip_id)
        all_ids.append(unit.trip_entity.trip_id)

    seen: set[str] = set()
    for tid in all_ids:
        assert tid not in seen, f"Duplicate trip ID: {tid}"
        seen.add(tid)

    print("PASS: unique_trip_ids")


def test_new_trip_metrics_reset():
    """New trip should start with reset metrics."""
    runner = _make_runner(fleet_size=1, num_ticks=15, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(15):
            runner.run_tick()

    unit = runner._vehicle_units["vehicle-001"]
    assert len(unit.completed_trips) >= 1

    completed = unit.completed_trips[0]
    current = unit.trip_entity

    # New trip should have significantly less accumulated metrics than completed trip
    assert current.distance_completed_km < completed.distance_completed_km
    assert current.fuel_consumed_liters < completed.fuel_consumed_liters
    assert current.duration_minutes < completed.duration_minutes
    assert current.status == TripStatus.IN_PROGRESS

    # New trip should have its own unique ID
    assert current.trip_id != completed.trip_id

    print("PASS: new_trip_metrics_reset")


def test_multiple_vehicles_complete_multiple_trips():
    """Multiple vehicles should each complete multiple trips."""
    runner = _make_runner(fleet_size=3, num_ticks=100, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(100):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        assert len(unit.completed_trips) >= 2, (
            f"{vehicle_id}: only {len(unit.completed_trips)} completed trips, "
            f"expected >= 2"
        )

    print("PASS: multiple_vehicles_complete_multiple_trips")


def test_1000_tick_simulation():
    """1,000-tick simulation should not crash and vehicles should cycle trips."""
    runner = _make_runner(fleet_size=2, num_ticks=1000, trip_distance_km=0.5)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(1000):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        assert len(unit.completed_trips) >= 2, (
            f"{vehicle_id}: only {len(unit.completed_trips)} completed trips"
        )
        assert unit.trip_entity.status == TripStatus.IN_PROGRESS

    print("PASS: 1000_tick_simulation")


def test_10000_tick_simulation():
    """10,000-tick simulation should not crash and vehicles should cycle trips."""
    runner = _make_runner(fleet_size=3, num_ticks=10000, trip_distance_km=2.0)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(10000):
            runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        total_trips = len(unit.completed_trips) + 1
        assert total_trips >= 3, (
            f"{vehicle_id}: only {total_trips} total trips in 10,000 ticks"
        )

        for trip in unit.completed_trips:
            assert trip.status == TripStatus.COMPLETED
            progress = (trip.distance_completed_km / trip.distance_planned_km) * 100
            assert progress <= 100.001

        assert unit.trip_entity.status == TripStatus.IN_PROGRESS

    print("PASS: 10000_tick_simulation")


def test_trip_id_format():
    """New trip IDs should follow the format vehicle-XXX-trip-NNNN."""
    runner = _make_runner(fleet_size=1, num_ticks=15, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(15):
            runner.run_tick()

    unit = runner._vehicle_units["vehicle-001"]
    assert len(unit.completed_trips) >= 1

    # First trip should be "trip-001" (from _build_fleet)
    assert unit.completed_trips[0].trip_id == "trip-001"

    # Subsequent trips should follow the format vehicle-XXX-trip-NNNN
    for i, trip in enumerate(unit.completed_trips[1:], start=1):
        expected = f"vehicle-001-trip-{i:04d}"
        assert trip.trip_id == expected, (
            f"Trip {i}: got {trip.trip_id}, expected {expected}"
        )

    # Current trip should also follow the format
    current = unit.trip_entity
    expected_current = f"vehicle-001-trip-{len(unit.completed_trips):04d}"
    assert current.trip_id == expected_current

    print("PASS: trip_id_format")


def test_trip_status_history():
    """Trips should record status transitions."""
    runner = _make_runner(fleet_size=1, num_ticks=15, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(15):
            runner.run_tick()

    unit = runner._vehicle_units["vehicle-001"]
    assert len(unit.completed_trips) >= 1

    completed = unit.completed_trips[0]
    assert len(completed.status_history) >= 2
    assert completed.status_history[0].status == TripStatus.IN_PROGRESS
    assert completed.status_history[-1].status == TripStatus.COMPLETED

    print("PASS: trip_status_history")


def test_analytics_with_trip_transitions():
    """Analytics should produce valid output across trip transitions."""
    from analytics.engine import AnalyticsEngine

    runner = _make_runner(fleet_size=2, num_ticks=50, trip_distance_km=0.1)
    analytics = AnalyticsEngine()

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(50):
            runner.run_tick()

            for vehicle_id in runner.vehicle_ids:
                unit = runner._vehicle_units[vehicle_id]
                if unit.last_packet is not None:
                    result = analytics.process(
                        unit.last_packet,
                        physics_result=unit.last_physics_result,
                        trip=unit.trip_entity,
                    )

                    tp = result["trip_performance"]
                    assert tp["status"] in ("in_progress", "not_initialized")

                    if tp["status"] == "in_progress":
                        assert 0 <= tp["progress_percent"] <= 100.0
                        assert tp["distance_remaining_km"] >= 0
                        assert tp["trip_id"] is not None

                    fe = result["fuel_efficiency"]
                    assert fe["status"] in ("ok", "unavailable")

    print("PASS: analytics_with_trip_transitions")


def test_completed_trip_preserves_final_metrics():
    """Completed trip should preserve its final accumulated metrics."""
    runner = _make_runner(fleet_size=1, num_ticks=15, trip_distance_km=0.1)

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        for _ in range(15):
            runner.run_tick()

    unit = runner._vehicle_units["vehicle-001"]
    assert len(unit.completed_trips) >= 1

    completed = unit.completed_trips[0]
    assert completed.distance_completed_km >= completed.distance_planned_km * 0.999
    assert completed.fuel_consumed_liters > 0
    assert completed.duration_minutes > 0
    assert completed.average_speed_kmh > 0
    assert completed.fuel_efficiency_km_per_liter > 0
    assert completed.end_time is not None

    print("PASS: completed_trip_preserves_final_metrics")


if __name__ == "__main__":
    test_trip_completes_exactly_at_destination()
    test_progress_never_exceeds_100_percent()
    test_remaining_distance_never_negative()
    test_completed_trips_have_correct_status()
    test_unique_trip_ids()
    test_new_trip_metrics_reset()
    test_multiple_vehicles_complete_multiple_trips()
    test_1000_tick_simulation()
    test_10000_tick_simulation()
    test_trip_id_format()
    test_trip_status_history()
    test_analytics_with_trip_transitions()
    test_completed_trip_preserves_final_metrics()
    print("\nALL TRIP LIFECYCLE TESTS PASSED")
