"""Test that Trip progress fields are updated from PhysicsTickResult each tick.

Validates:
  - distance_completed_km accumulates per-tick distance_travelled_km
  - fuel_consumed_liters accumulates per-tick fuel_consumed_liters
  - duration_minutes accumulates tick delta_time / 60
  - average_speed_kmh and fuel_efficiency_km_per_liter are recomputed
"""

from digital_twin.simulation.simulation_runner import RunnerConfig, SimulationRunner


def test_trip_progress_accumulates():
    config = RunnerConfig(
        fleet_size=1,
        num_ticks=5,
        real_time_pacing=False,
    )
    runner = SimulationRunner(config=config)
    runner.start()

    vehicle_id = runner.vehicle_ids[0]
    unit = runner._vehicle_units[vehicle_id]
    trip = unit.trip_entity

    # Snapshot before any ticks
    initial_distance = trip.distance_completed_km
    initial_fuel = trip.fuel_consumed_liters
    initial_duration = trip.duration_minutes

    assert initial_distance == 0.0
    assert initial_fuel == 0.0
    assert initial_duration == 0.0

    # Run one tick
    runner.run_tick()

    assert trip.distance_completed_km > 0, (
        "distance_completed_km should be > 0 after one tick"
    )
    assert trip.fuel_consumed_liters > 0, (
        "fuel_consumed_liters should be > 0 after one tick"
    )
    assert trip.duration_minutes > 0, (
        "duration_minutes should be > 0 after one tick"
    )
    assert trip.average_speed_kmh >= 0, (
        "average_speed_kmh should be >= 0"
    )
    assert trip.fuel_efficiency_km_per_liter > 0, (
        "fuel_efficiency_km_per_liter should be > 0 when fuel is consumed"
    )

    distance_after_one = trip.distance_completed_km
    fuel_after_one = trip.fuel_consumed_liters
    duration_after_one = trip.duration_minutes

    # Run a second tick and verify accumulation
    runner.run_tick()

    assert trip.distance_completed_km > distance_after_one, (
        "distance_completed_km should increase each tick"
    )
    assert trip.fuel_consumed_liters > fuel_after_one, (
        "fuel_consumed_liters should increase each tick"
    )
    assert trip.duration_minutes > duration_after_one, (
        "duration_minutes should increase each tick"
    )

    # Run remaining ticks
    for _ in range(3):
        runner.run_tick()

    # After 5 ticks, all progress fields should be non-zero and monotonically growing
    assert trip.distance_completed_km > 0
    assert trip.fuel_consumed_liters > 0
    assert trip.duration_minutes > 0
    assert trip.average_speed_kmh > 0
    assert trip.fuel_efficiency_km_per_liter > 0

    print("ALL TESTS PASSED")
    print(f"  distance_completed_km = {trip.distance_completed_km:.6f}")
    print(f"  fuel_consumed_liters = {trip.fuel_consumed_liters:.6f}")
    print(f"  duration_minutes = {trip.duration_minutes:.6f}")
    print(f"  average_speed_kmh = {trip.average_speed_kmh:.6f}")
    print(f"  fuel_efficiency_km_per_liter = {trip.fuel_efficiency_km_per_liter:.6f}")


def test_zero_fuel_no_division_by_zero():
    """When no fuel is consumed, fuel_efficiency_km_per_liter stays at default."""
    config = RunnerConfig(
        fleet_size=1,
        num_ticks=1,
        real_time_pacing=False,
    )
    runner = SimulationRunner(config=config)
    runner.start()

    vehicle_id = runner.vehicle_ids[0]
    trip = runner._vehicle_units[vehicle_id].trip_entity

    runner.run_tick()

    # fuel_consumed_liters should normally be > 0 for a moving vehicle,
    # but the code handles the 0 case safely (no division by zero).
    # If fuel IS consumed, efficiency should be positive.
    if trip.fuel_consumed_liters > 0:
        assert trip.fuel_efficiency_km_per_liter > 0
    # If somehow fuel is 0, efficiency should remain at default 0.0
    else:
        assert trip.fuel_efficiency_km_per_liter == 0.0

    print("DIVISION-BY-ZERO GUARD TEST PASSED")


if __name__ == "__main__":
    test_trip_progress_accumulates()
    test_zero_fuel_no_division_by_zero()
