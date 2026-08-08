"""
Resilience of the fleet tick loop against tick-level failures.

A single failing telemetry consumer (analytics, persistence, WebSocket)
or a single failing tick must be observable and must never terminate
``runtime.run()``. The loop may halt only when the fleet model itself
fails repeatedly (genuinely unrecoverable), so the runtime never spins
silently. These tests verify:

  * a raising consumer does not propagate out of ``TelemetryPipeline.publish``
    and does not starve consumers registered after it,
  * ``runtime.run()`` survives a consumer that raises on every sample and
    still completes every trip and every flush callback,
  * the failures are logged with context (never swallowed silently),
  * ``runtime.run()`` halts after ``MAX_CONSECUTIVE_TICK_FAILURES`` when the
    fleet model raises on every tick instead of spinning forever.
"""

import asyncio
import logging
from datetime import datetime
from types import SimpleNamespace

from backend.analytics.context.analytics_context import AnalyticsContext
from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.pipeline.telemetry_pipeline import TelemetryPipeline
from backend.telemetry.models.telemetry_sample import TelemetrySample


def _make_sample(vehicle_id="V-1", driver_id="D-1", trip_id="T-1"):
    return TelemetrySample(
        timestamp=datetime(2026, 8, 7, 10, 0, tzinfo=None),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        speed_kmh=50.0,
        rpm=2200.0,
        throttle_position_percent=30.0,
        brake_pressure=0.0,
        coolant_temperature_c=90.0,
        engine_load_percent=55.0,
        fuel_rate_lph=7.0,
        fuel_level_percent=80.0,
        odometer_km=1001.0,
    )


class _RaisingConsumer:
    """A telemetry consumer that raises on every sample."""

    def __init__(self, name="raising"):
        self.name = name
        self.calls = 0
        self.vehicles = set()

    def consume(self, sample):
        self.calls += 1
        self.vehicles.add(sample.vehicle_id)
        raise RuntimeError(f"{self.name} exploded on {sample.vehicle_id}")


class _RecordingConsumer:
    """A telemetry consumer that records every sample it receives."""

    def __init__(self, name="recording"):
        self.name = name
        self.samples = []

    def consume(self, sample):
        self.samples.append(sample)


class _StubPersistence:
    """In-memory stand-in for PersistenceService (async no-ops)."""

    async def _noop(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self._noop


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


def _build_fleet(specs):
    fleet = FleetRunner(tick_seconds=1.0)
    trips = []
    for vid, did, rid, tid, fuel, distance in specs:
        vehicle = Vehicle(
            vehicle_id=vid,
            make="Ford",
            model="Transit",
            year=2023,
            odometer_km=1000.0,
            fuel_level_percent=fuel,
        )
        driver = Driver(
            driver_id=did,
            name="Test Driver",
            behavior_profile=BehaviorProfile.CAUTIOUS,
        )
        route = Route(
            route_id=rid,
            origin="Warehouse",
            destination="Customer A",
            distance_km=distance,
            route_type=RouteType.URBAN,
            speed_limit_kmh=60.0,
        )
        trip = Trip(trip_id=tid, vehicle_id=vid, driver_id=did, route_id=rid)
        trips.append(trip)
        fleet.add_assignment(
            assignment=Assignment(
                assignment_id=f"A-{vid}",
                driver_id=did,
                vehicle_id=vid,
                route_id=rid,
            ),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
    return fleet, trips


class TestTelemetryPipelineIsolation:
    def test_failing_consumer_does_not_raise_or_starve(self):
        pipeline = TelemetryPipeline()
        good_before = _RecordingConsumer("good-before")
        bad = _RaisingConsumer("bad")
        good_after = _RecordingConsumer("good-after")
        pipeline.register(good_before)
        pipeline.register(bad)
        pipeline.register(good_after)

        sample = _make_sample()
        pipeline.publish(sample)

        assert bad.calls == 1
        assert good_before.samples == [sample]
        assert good_after.samples == [sample]

    def test_later_consumers_still_receive_following_samples(self):
        pipeline = TelemetryPipeline()
        bad = _RaisingConsumer("bad")
        good = _RecordingConsumer("good")
        pipeline.register(bad)
        pipeline.register(good)

        for i in range(5):
            pipeline.publish(_make_sample())

        assert bad.calls == 5
        assert len(good.samples) == 5


class TestRuntimeSurvivesTickFailures:
    def test_run_survives_consumer_that_raises_on_every_sample(self, caplog):
        caplog.set_level(logging.ERROR)

        async def _scenario():
            runtime = DriveVitalsRuntime(
                tick_seconds=1.0,
                persistence_service=_StubPersistence(),
            )
            for vid, did, tid, rid in [
                ("V-1", "D-1", "T-1", "R-1"),
                ("V-2", "D-2", "T-2", "R-2"),
            ]:
                runtime._context_store.register(
                    AnalyticsContext(
                        vehicle_id=vid,
                        driver_id=did,
                        trip_id=tid,
                        route_id=rid,
                        route_type="urban",
                        speed_limit_kmh=60.0,
                        vehicle_make="Ford",
                        vehicle_model="Transit",
                        vehicle_year=2023,
                    )
                )

            fleet, trips = _build_fleet(
                [
                    ("V-1", "D-1", "R-1", "T-1", 90.0, 0.1),
                    ("V-2", "D-2", "R-2", "T-2", 80.0, 0.2),
                ]
            )
            runtime._fleet = fleet

            bad = _RaisingConsumer("bad")
            good = _RecordingConsumer("good")
            runtime.telemetry_pipeline.register(bad)
            runtime.telemetry_pipeline.register(good)

            completed_trips = []

            def dashboard_callback(summary, context, runtime_state, all_events, trip):
                completed_trips.append(trip)

            runtime.set_trip_flush_callback(dashboard_callback)

            real_sleep = asyncio.sleep

            async def fast_sleep(delay):
                await real_sleep(0)

            asyncio.sleep = fast_sleep
            try:
                await runtime.run()
            finally:
                asyncio.sleep = real_sleep

            await _drain_pending_tasks()

            # The bad consumer raised for every sample and the loop survived.
            assert bad.calls > 0
            assert bad.vehicles == {"V-1", "V-2"}

            # Consumers registered after the bad one were not starved: the
            # good consumer received samples from every vehicle.
            assert {s.vehicle_id for s in good.samples} == {"V-1", "V-2"}

            # The lifecycle completed normally: every trip ended.
            assert [t.status for t in trips] == [
                TripStatus.COMPLETED,
                TripStatus.COMPLETED,
            ]
            assert fleet.active_runners() == []
            assert sorted(t.trip_id for t in completed_trips) == ["T-1", "T-2"]

            # The failure was logged with context, not swallowed silently.
            assert "Telemetry consumer _RaisingConsumer failed" in caplog.text

        asyncio.run(_scenario())

    def test_run_halts_after_repeated_tick_model_failures(self):
        """A persistently failing fleet model halts the loop instead of
        spinning forever."""

        class _RaisingFleet:
            def __init__(self, runners):
                self._runners = runners
                self.tick_calls = 0

            def start_all(self, now=None):
                pass

            def active_runners(self):
                return self._runners

            def tick_all(self, now=None):
                self.tick_calls += 1
                raise RuntimeError("fleet model exploded")

        async def _scenario():
            runtime = DriveVitalsRuntime(
                tick_seconds=1.0,
                persistence_service=None,
            )
            runtime._fleet = _RaisingFleet(
                [
                    SimpleNamespace(
                        vehicle=SimpleNamespace(
                            vehicle_id="V-1",
                            fuel_level_percent=90.0,
                        )
                    )
                ]
            )
            runtime.MAX_CONSECUTIVE_TICK_FAILURES = 3

            real_sleep = asyncio.sleep

            async def fast_sleep(delay):
                await real_sleep(0)

            asyncio.sleep = fast_sleep
            try:
                await runtime.run()
            finally:
                asyncio.sleep = real_sleep

            # Exactly the threshold of failed ticks, then a clean halt.
            assert runtime._fleet.tick_calls == 3

        asyncio.run(_scenario())


class TestRuntimeCompletionIsolation:
    def test_one_failing_completion_does_not_starve_others(self, caplog):
        caplog.set_level(logging.ERROR)

        async def _scenario():
            runtime = DriveVitalsRuntime(
                tick_seconds=1.0,
                persistence_service=_StubPersistence(),
            )
            for vid, did, tid, rid in [
                ("V-1", "D-1", "T-1", "R-1"),
                ("V-2", "D-2", "T-2", "R-2"),
            ]:
                runtime._context_store.register(
                    AnalyticsContext(
                        vehicle_id=vid,
                        driver_id=did,
                        trip_id=tid,
                        route_id=rid,
                        route_type="urban",
                        speed_limit_kmh=60.0,
                        vehicle_make="Ford",
                        vehicle_model="Transit",
                        vehicle_year=2023,
                    )
                )

            fleet, trips = _build_fleet(
                [
                    ("V-1", "D-1", "R-1", "T-1", 90.0, 0.1),
                    ("V-2", "D-2", "R-2", "T-2", 80.0, 0.2),
                ]
            )
            runtime._fleet = fleet

            # V-2's completion callback raises; V-1 must still complete.
            def flaky_callback(summary, context, runtime_state, all_events, trip):
                if summary.vehicle_id == "V-2":
                    raise RuntimeError("flaky websocket callback")
                trip._flushed = True

            runtime.set_trip_flush_callback(flaky_callback)

            real_sleep = asyncio.sleep

            async def fast_sleep(delay):
                await real_sleep(0)

            asyncio.sleep = fast_sleep
            try:
                await runtime.run()
            finally:
                asyncio.sleep = real_sleep

            await _drain_pending_tasks()

            # Both trips transitioned to completed even though one flush failed.
            assert [t.status for t in trips] == [
                TripStatus.COMPLETED,
                TripStatus.COMPLETED,
            ]
            assert trips[0]._flushed is True
            assert not hasattr(trips[1], "_flushed")

            assert "Trip completion handling failed for vehicle=V-2" in caplog.text

        asyncio.run(_scenario())
