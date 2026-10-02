"""M5.2 regression tests for the Digital Twin scenario parameters.

The forensic audit found three decorative fields:

* ``seed``             — stored, displayed and logged, but never reached
  the telemetry generator (the runtime seeded the OBD generators from a
  per-process-salted ``hash()`` of a random uuid, and assigned
  ``run_seed`` *after* the generators were already built).
* ``simulation_speed`` — persisted and rendered as "Nx" but never used.
* ``duration_seconds`` — persisted and rendered but never enforced.

These tests pin the corrected behaviour: a seed reproduces the telemetry
values, a speed multiplier changes wall-clock pacing, and a duration
actually ends the run.
"""

import asyncio
import time
from datetime import datetime, timezone

from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.vehicle_runner import VehicleRunner
from backend.telemetry.models.telemetry_sample import TelemetrySample

START = datetime(2026, 9, 26, 8, 0, tzinfo=timezone.utc)


class _RecordingFleet:
    """Fleet wrapper that runs real ``VehicleRunner``s and records every
    generated sample, so a run can be driven a bounded number of ticks
    without depending on route completion."""

    def __init__(self, runners: list) -> None:
        self._runners = runners
        self.samples: list[TelemetrySample] = []
        self.ticks = 0

    # -- FleetRunner-compatible surface used by DriveVitalsRuntime ----

    def start_all(self, now=None) -> None:
        for runner in self._runners:
            runner.start(now=now)

    def active_runners(self) -> list:
        return [r for r in self._runners if not r.is_complete()]

    def tick_all(self, now=None) -> list[TelemetrySample]:
        produced: list[TelemetrySample] = []
        for runner in self.active_runners():
            sample = runner.tick(now=now)
            produced.append(sample)
            self.samples.append(sample)
        self.ticks += 1
        return produced


def _runner(vehicle_id: str, distance_km: float = 400.0) -> VehicleRunner:
    vehicle = Vehicle(
        vehicle_id=vehicle_id,
        make="Ford",
        model="Transit",
        year=2024,
        fuel_efficiency_factor=1.0,
        acceleration_response=1.0,
        tank_capacity_liters=60.0,
    )
    driver = Driver(
        driver_id=f"d-{vehicle_id}",
        name="Test Driver",
        behavior_profile=BehaviorProfile.STANDARD,
    )
    route = Route(
        route_id=f"r-{vehicle_id}",
        origin="A",
        destination="B",
        distance_km=distance_km,
        route_type=RouteType.URBAN,
        speed_limit_kmh=50.0,
    )
    trip = Trip(
        trip_id=f"t-{vehicle_id}",
        vehicle_id=vehicle_id,
        driver_id=driver.driver_id,
        route_id=route.route_id,
    )
    return VehicleRunner(
        vehicle=vehicle,
        driver=driver,
        route=route,
        trip=trip,
    )


def _runtime(tick_seconds: float) -> tuple[DriveVitalsRuntime, _RecordingFleet]:
    runtime = DriveVitalsRuntime(tick_seconds=tick_seconds)
    fleet = _RecordingFleet([_runner("v-seed-1")])
    runtime._fleet = fleet
    return runtime, fleet


def _telemetry_shape(samples: list[TelemetrySample]) -> list[tuple]:
    """The generated values only: timestamps and trip ids differ per run."""
    return [
        (
            s.speed_kmh,
            s.rpm,
            s.throttle_position_percent,
            s.brake_pressure,
            s.coolant_temperature_c,
            s.fuel_rate_lph,
        )
        for s in samples
    ]



class TestSeedIsFunctional:
    async def test_same_seed_reproduces_identical_telemetry(self) -> None:
        first_runtime, first_fleet = _runtime(tick_seconds=1.0)
        await first_runtime.run(seed=4242, duration_seconds=5)

        second_runtime, second_fleet = _runtime(tick_seconds=1.0)
        await second_runtime.run(seed=4242, duration_seconds=5)

        assert first_fleet.ticks == 5
        assert _telemetry_shape(first_fleet.samples) == _telemetry_shape(
            second_fleet.samples
        )

    async def test_different_seed_changes_telemetry(self) -> None:
        first_runtime, first_fleet = _runtime(tick_seconds=1.0)
        await first_runtime.run(seed=1, duration_seconds=5)

        second_runtime, second_fleet = _runtime(tick_seconds=1.0)
        await second_runtime.run(seed=2, duration_seconds=5)

        assert _telemetry_shape(first_fleet.samples) != _telemetry_shape(
            second_fleet.samples
        )

    async def test_seed_propagates_to_the_runners(self) -> None:
        runtime, fleet = _runtime(tick_seconds=1.0)
        await runtime.run(seed=777, duration_seconds=1)

        assert fleet.ticks == 1
        # The runtime must assign the run seed before the runners start so
        # every runner rebuilds its generator from it.
        assert fleet._runners[0].run_seed == 777

    async def test_unseeded_runs_still_vary(self) -> None:
        """Without a scenario seed the run id keeps runs distinct."""
        first_runtime, first_fleet = _runtime(tick_seconds=1.0)
        await first_runtime.run(duration_seconds=5)

        second_runtime, second_fleet = _runtime(tick_seconds=1.0)
        await second_runtime.run(duration_seconds=5)

        assert _telemetry_shape(first_fleet.samples) != _telemetry_shape(
            second_fleet.samples
        )


class TestSimulationSpeedIsFunctional:
    async def test_speed_multiplier_shortens_wall_clock_pacing(self) -> None:
        slow_runtime, slow_fleet = _runtime(tick_seconds=0.05)
        started = time.monotonic()
        await slow_runtime.run(duration_seconds=0.5, simulation_speed=1.0)
        slow_elapsed = time.monotonic() - started

        fast_runtime, fast_fleet = _runtime(tick_seconds=0.05)
        started = time.monotonic()
        await fast_runtime.run(duration_seconds=0.5, simulation_speed=10.0)
        fast_elapsed = time.monotonic() - started

        # Same simulated workload and identical tick count...
        assert slow_fleet.ticks == fast_fleet.ticks == 10
        # ...but ten times the pacing means much less wall-clock time.
        assert fast_elapsed < slow_elapsed / 2, (
            f"speed=10 took {fast_elapsed:.3f}s, speed=1 took "
            f"{slow_elapsed:.3f}s: simulation_speed does not control pacing"
        )

    async def test_invalid_speed_falls_back_to_real_time(self) -> None:
        runtime, fleet = _runtime(tick_seconds=0.01)
        await runtime.run(duration_seconds=0.1, simulation_speed=0.0)

        assert fleet.ticks == 10


class TestDurationIsEnforced:
    async def test_run_ends_when_the_configured_duration_elapses(self) -> None:
        runtime, fleet = _runtime(tick_seconds=1.0)
        await runtime.run(duration_seconds=3)

        assert fleet.ticks == 3

    async def test_run_continues_without_a_duration(self) -> None:
        runtime, _fleet = _runtime(tick_seconds=0.01)
        task = asyncio.create_task(runtime.run())

        for _ in range(5):
            await asyncio.sleep(0.01)
        assert not task.done(), "an open-ended run must not stop by itself"

        runtime.stop()
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.CancelledError:
            pass

    async def test_duration_leaves_trips_as_a_manual_stop_would(self) -> None:
        """Stopping on duration must not complete trips early."""
        runtime, fleet = _runtime(tick_seconds=1.0)
        await runtime.run(duration_seconds=2)

        runner = fleet._runners[0]
        assert not runner.is_complete()
        assert runner.trip.distance_travelled_km < runner.route.distance_km
