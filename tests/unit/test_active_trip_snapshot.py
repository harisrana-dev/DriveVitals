"""
Unit tests for the M3 active-trip snapshot stream.

Verifies the active-trip WebSocket contract end to end through the real
``DriveVitalsRuntime`` tick loop (sleep stubbed to be deterministic):

  * one batch per tick containing only the current active set,
  * active snapshots never expose completion-only fields,
  * live metrics (distance, duration) progress monotonically,
  * a batch never exceeds the number of active vehicles,
  * trips that complete are excluded from all later active batches,
  * the runtime status guard (STARTED/IN_PROGRESS) is what excludes
    aborted/assigned trips — not the fleet ``active_runners`` filter,
  * the builder serializes accumulated behaviour events as dicts.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.state.runtime_state import (
    RuntimeAnalyticsState,
)
from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.trips.services.active_trip_builder import (
    build_active_trip_snapshot,
)

START_TIME = datetime(2026, 8, 7, 10, 0, 0, tzinfo=timezone.utc)


class _StubPersistence:
    """In-memory stand-in for PersistenceService; every write is a no-op."""

    async def _noop(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self._noop


def _make_context(vehicle_id, driver_id, trip_id, route_id):
    return AnalyticsContext(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        route_id=route_id,
        route_type="urban",
        speed_limit_kmh=60.0,
        route_name="Warehouse \u2192 Customer A",
        vehicle_make="Ford",
        vehicle_model="Transit",
        vehicle_year=2023,
        driver_name="Test Driver",
    )


def _build_fleet(specs, tick_seconds=1.0):
    """Build a FleetRunner with one assignment per spec.

    Spec tuple: (vehicle_id, driver_id, route_id, trip_id, fuel_pct, route_km)
    """
    fleet = FleetRunner(tick_seconds=tick_seconds)
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
        trip = Trip(
            trip_id=tid,
            vehicle_id=vid,
            driver_id=did,
            route_id=rid,
        )
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


def _register_contexts(runtime, specs):
    for vid, did, rid, tid, _fuel, _distance in specs:
        runtime._context_store.register(
            _make_context(vid, did, tid, rid)
        )


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


class _FastSleep:
    """Context manager swapping asyncio.sleep for an instant yield."""

    def __enter__(self):
        self._real_sleep = asyncio.sleep

        async def fast_sleep(_delay):
            await self._real_sleep(0)

        asyncio.sleep = fast_sleep
        return self

    def __exit__(self, *exc):
        asyncio.sleep = self._real_sleep


def test_build_active_trip_snapshot_contract():
    """The builder exposes authoritative live state and no fabrication."""
    started_at = START_TIME
    now = started_at + timedelta(minutes=10)

    trip = Trip(
        trip_id="T-1",
        vehicle_id="V-1",
        driver_id="D-1",
        route_id="R-1",
        status=TripStatus.IN_PROGRESS,
        started_at=started_at,
        distance_travelled_km=5.0,
        maximum_speed_kmh=74.0,
    )
    context = _make_context("V-1", "D-1", "T-1", "R-1")
    runtime_state = RuntimeAnalyticsState(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        timestamp=now,
        speed_kmh=52.0,
        rpm=2300.0,
        throttle_position_percent=40.0,
        brake_pressure=0.5,
        coolant_temperature_c=88.0,
        engine_load_percent=45.0,
        fuel_rate_lph=6.0,
        fuel_level_percent=72.0,
        odometer_km=1000.0,
    )
    behaviour = DriverBehaviourAnalysis(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        speeding=False,
        speed_excess_kmh=0.0,
        harsh_braking=False,
        aggressive_throttle=True,
        high_rpm=False,
        severity="moderate",
        odometer_km=1000.0,
    )
    summary = DriverBehaviourSummary(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        total_distance_km=5.0,
        speeding_event_count=1,
        speeding_duration_seconds=30.0,
        speeding_distance_km=0.4,
        maximum_speed_excess_kmh=12.0,
        harsh_braking_count=0,
        aggressive_throttle_event_count=2,
        aggressive_throttle_duration_seconds=8.0,
        high_rpm_event_count=0,
        high_rpm_duration_seconds=0.0,
        severe_event_count=0,
        moderate_event_count=3,
        minor_event_count=0,
        overall_severity="moderate",
    )
    events = [
        BehaviourEvent(
            vehicle_id="V-1",
            driver_id="D-1",
            trip_id="T-1",
            event_type="speeding",
            started_at=started_at,
            ended_at=started_at + timedelta(seconds=30),
            duration_seconds=30.0,
            distance_km=0.4,
            severity="moderate",
            max_speed_excess_kmh=12.0,
        )
    ]

    snap = build_active_trip_snapshot(
        trip=trip,
        context=context,
        runtime_state=runtime_state,
        behaviour=behaviour,
        active_event_types=("aggressive_throttle",),
        summary=summary,
        events=events,
        fuel_consumed_liters=1.8,
        now=now,
    )

    assert snap.trip_id == "T-1"
    assert snap.status == "in_progress"
    assert snap.vehicle_id == "V-1"
    assert snap.driver_id == "D-1"
    assert snap.vehicle_name == "2023 Ford Transit"
    assert snap.driver_name == "Test Driver"
    assert snap.route_id == "R-1"
    assert snap.route_type == "urban"
    assert snap.route_name == "Warehouse \u2192 Customer A"

    assert snap.distance_km == 5.0
    assert snap.duration_seconds == 600.0
    assert snap.average_speed_kmh == 30.0
    assert snap.maximum_speed_kmh == 74.0
    assert snap.fuel_consumed_liters == 1.8
    assert snap.average_fuel_rate_lph == 10.8
    assert snap.current_speed_kmh == 52.0
    assert snap.speeding is False
    assert snap.harsh_braking is False
    assert snap.aggressive_throttle is True
    assert snap.high_rpm is False

    assert snap.safety_score is None
    assert snap.grade is None
    assert snap.completed_at is None
    assert snap.started_at == started_at

    assert snap.speeding_event_count == 1
    assert snap.speeding_duration_seconds == 30.0
    assert snap.aggressive_throttle_event_count == 2
    assert snap.aggressive_throttle_duration_seconds == 8.0
    assert snap.overall_severity == "moderate"

    assert len(snap.events) == 1
    evt = snap.events[0]
    assert evt["event_type"] == "speeding"
    assert evt["label"] == "Speeding"
    assert evt["started_at"] == started_at.isoformat()
    assert evt["ended_at"] == (started_at + timedelta(seconds=30)).isoformat()
    assert evt["duration_seconds"] == 30.0
    assert evt["distance_km"] == 0.4
    assert evt["severity"] == "moderate"


def test_build_active_trip_snapshot_no_fabricated_values():
    """With nothing live yet, the builder stays honestly unset."""
    started_at = START_TIME
    now = started_at + timedelta(minutes=2)

    trip = Trip(
        trip_id="T-2",
        vehicle_id="V-2",
        driver_id="D-2",
        route_id="R-2",
        status=TripStatus.STARTED,
        started_at=started_at,
    )
    context = _make_context("V-2", "D-2", "T-2", "R-2")

    snap = build_active_trip_snapshot(
        trip=trip,
        context=context,
        now=now,
    )

    assert snap.status == "in_progress"
    assert snap.distance_km == 0.0
    assert snap.duration_seconds == 120.0
    assert snap.average_speed_kmh == 0.0
    assert snap.maximum_speed_kmh == 0.0
    assert snap.fuel_consumed_liters == 0.0
    assert snap.average_fuel_rate_lph == 0.0
    assert snap.current_speed_kmh is None
    assert snap.speeding is False
    assert snap.harsh_braking is False
    assert snap.aggressive_throttle is False
    assert snap.high_rpm is False
    assert snap.speeding_event_count == 0
    assert snap.harsh_braking_count == 0
    assert snap.overall_severity == "normal"
    assert snap.events == ()
    assert snap.safety_score is None
    assert snap.grade is None
    assert snap.completed_at is None


def test_publish_active_trip_updates_status_guard():
    """Only STARTED/IN_PROGRESS trips are streamed; the guard is not the
    fleet ``active_runners`` filter (which keeps aborted runners active)."""

    async def _scenario():
        runtime = DriveVitalsRuntime(tick_seconds=1.0, persistence_service=None)
        specs = [("V-1", "D-1", "R-1", "T-1", 90.0, 50.0)]
        _register_contexts(runtime, specs)
        fleet, trips = _build_fleet(specs)
        runtime._fleet = fleet

        batches = []
        runtime.set_trip_update_callback(
            lambda snapshots, now: batches.append(list(snapshots))
        )

        fleet.start_all(now=START_TIME)

        # STARTED is streamed.
        runtime._publish_active_trip_updates(now=START_TIME)
        assert len(batches) == 1
        assert [s.trip_id for s in batches[0]] == ["T-1"]
        assert batches[0][0].status == "in_progress"

        # IN_PROGRESS is streamed.
        trips[0].advance(0.1)
        runtime._publish_active_trip_updates(
            now=START_TIME + timedelta(seconds=1)
        )
        assert len(batches) == 2

        # ABORTED is excluded by the runtime guard even though the fleet
        # still reports it as an active runner.
        trips[0].abort(at=START_TIME + timedelta(seconds=2))
        assert fleet.active_runners()
        runtime._publish_active_trip_updates(
            now=START_TIME + timedelta(seconds=2)
        )
        assert len(batches) == 2

        # COMPLETED is excluded.
        trips[0].status = TripStatus.IN_PROGRESS
        trips[0].completed_at = None
        trips[0].distance_travelled_km = 50.0
        trips[0].complete(
            ending_odometer_km=1000.0,
            at=START_TIME + timedelta(seconds=3),
        )
        runtime._publish_active_trip_updates(
            now=START_TIME + timedelta(seconds=3)
        )
        assert len(batches) == 2

        # ASSIGNED (never started) is excluded.
        trips[0].status = TripStatus.ASSIGNED
        trips[0].started_at = None
        runtime._publish_active_trip_updates(
            now=START_TIME + timedelta(seconds=4)
        )
        assert len(batches) == 2

    asyncio.run(_scenario())


def test_publish_active_trip_updates_isolates_failing_vehicle():
    """A snapshot failure for one vehicle never starves the others."""

    async def _scenario():
        runtime = DriveVitalsRuntime(tick_seconds=1.0, persistence_service=None)
        specs = [
            ("V-1", "D-1", "R-1", "T-1", 90.0, 50.0),
            ("V-2", "D-2", "R-2", "T-2", 80.0, 50.0),
        ]
        # V-2 has no analytics context, so its snapshot must be skipped.
        _register_contexts(runtime, [specs[0]])
        fleet, trips = _build_fleet(specs)
        runtime._fleet = fleet

        batches = []
        runtime.set_trip_update_callback(
            lambda snapshots, now: batches.append(list(snapshots))
        )

        fleet.start_all(now=START_TIME)
        runtime._publish_active_trip_updates(now=START_TIME)

        assert len(batches) == 1
        assert [s.trip_id for s in batches[0]] == ["T-1"]

    asyncio.run(_scenario())


def test_runtime_active_stream_updates_in_realtime():
    """The tick loop streams live updates with a strictly growing trip
    state, bounded by the number of active vehicles."""

    async def _scenario():
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=_StubPersistence(),
        )
        specs = [
            ("V-1", "D-1", "R-1", "T-1", 90.0, 50.0),
            ("V-2", "D-2", "R-2", "T-2", 80.0, 50.0),
        ]
        _register_contexts(runtime, specs)
        fleet, trips = _build_fleet(specs)
        runtime._fleet = fleet

        batches = []

        def on_update(snapshots, now):
            batches.append(list(snapshots))
            if len(batches) >= 4:
                runtime.stop()

        runtime.set_trip_update_callback(on_update)

        with _FastSleep():
            await runtime.run()

        await _drain_pending_tasks()

        assert len(batches) == 4
        assert all(len(batch) == 2 for batch in batches)
        assert all(
            {s.trip_id for s in batch} == {"T-1", "T-2"}
            for batch in batches
        )

        for batch in batches:
            for snap in batch:
                assert snap.status == "in_progress"
                assert snap.safety_score is None
                assert snap.grade is None
                assert snap.completed_at is None
                assert snap.started_at is not None
                assert snap.distance_km >= 0.0
                assert snap.duration_seconds >= 0.0
                assert snap.average_speed_kmh >= 0.0
                assert snap.current_speed_kmh is not None
                assert snap.current_speed_kmh >= 0.0

        for trip_id in ("T-1", "T-2"):
            distances = [
                next(s.distance_km for s in b if s.trip_id == trip_id)
                for b in batches
            ]
            durations = [
                next(s.duration_seconds for s in b if s.trip_id == trip_id)
                for b in batches
            ]
            assert distances[0] < distances[-1]
            assert durations[0] < durations[-1]
            assert all(
                distances[i] < distances[i + 1]
                for i in range(len(distances) - 1)
            )
            assert all(
                durations[i] < durations[i + 1]
                for i in range(len(durations) - 1)
            )

        assert all(t.status == TripStatus.IN_PROGRESS for t in trips)

    asyncio.run(_scenario())


def test_runtime_active_stream_excludes_completed_trips():
    """A trip that completes moves to history and never reappears in the
    active stream, while the remaining trip keeps streaming."""

    async def _scenario():
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=_StubPersistence(),
        )
        specs = [
            ("V-1", "D-1", "R-1", "T-1", 90.0, 0.05),
            ("V-2", "D-2", "R-2", "T-2", 80.0, 50.0),
        ]
        _register_contexts(runtime, specs)
        fleet, trips = _build_fleet(specs)
        runtime._fleet = fleet

        log = []

        def on_update(snapshots, now):
            log.append(("update", {s.trip_id for s in snapshots}))
            seen_completed = False
            updates_after_completion = 0
            for kind, payload in log:
                if kind == "completed" and payload == "T-1":
                    seen_completed = True
                elif kind == "update" and seen_completed:
                    updates_after_completion += 1
            if seen_completed and updates_after_completion >= 2:
                runtime.stop()

        def on_flush(summary, context, runtime_state, all_events, trip):
            log.append(("completed", trip.trip_id))

        runtime.set_trip_update_callback(on_update)
        runtime.set_trip_flush_callback(on_flush)

        with _FastSleep():
            await runtime.run()

        await _drain_pending_tasks()

        completion_pos = next(
            i
            for i, (kind, payload) in enumerate(log)
            if kind == "completed" and payload == "T-1"
        )

        pre_updates = [
            ids for kind, ids in log[:completion_pos] if kind == "update"
        ]
        assert any("T-1" in ids for ids in pre_updates)
        assert any(ids == {"T-1", "T-2"} for ids in pre_updates)

        post_updates = [
            ids for kind, ids in log[completion_pos:] if kind == "update"
        ]
        assert len(post_updates) >= 2
        assert all("T-1" not in ids for ids in post_updates)
        assert all("T-2" in ids for ids in post_updates)

        assert trips[0].status == TripStatus.COMPLETED
        assert trips[1].status == TripStatus.IN_PROGRESS

    asyncio.run(_scenario())
