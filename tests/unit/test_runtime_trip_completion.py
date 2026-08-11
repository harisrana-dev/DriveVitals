"""
Regression tests for the runtime trip-completion persistence callback.

Commit b14b838 extended the trip-flush callback contract to five positional
arguments (summary, context, runtime_state, all_events, trip) at the call site
in ``DriveVitalsRuntime.run()``, but the ``_persist_trip_completion`` callback
registered by ``run()`` was not updated and still declared four parameters.
The first completed trip therefore raised ``TypeError``, which killed the
``runtime.run()`` task, stopped all fleet updates and dashboard publishing,
and left every trip stuck ``in_progress`` in the database.

These tests verify:
  * the registered completion callback accepts the five-argument contract,
  * multiple trip completions are processed without raising,
  * ``PersistenceService.complete_trip`` is scheduled for every completion
    (the persistence-side ``in_progress`` -> ``completed`` transition),
  * the pre-existing (dashboard) callback still receives its five arguments,
  * the full ``run()`` loop survives several trip completions, exits
    cleanly, and leaves no active runners behind.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.fleet.runtime.runtime_state import RuntimeState


class _StubPersistence:
    """In-memory stand-in for PersistenceService.

    Explicitly records ``create_trip``/``complete_trip``; every other
    persistence method is an async no-op via ``__getattr__``.
    """

    def __init__(self):
        self.create_trip_calls = []
        self.complete_trip_calls = []

    async def create_trip(self, **kwargs):
        self.create_trip_calls.append(kwargs)

    async def complete_trip(self, **kwargs):
        self.complete_trip_calls.append(kwargs)

    async def _noop(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self._noop


def _make_summary(vehicle_id, trip_id, driver_id, distance_km):
    return DriverBehaviourSummary(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        total_distance_km=distance_km,
        speeding_event_count=0,
        speeding_duration_seconds=0.0,
        speeding_distance_km=0.0,
        maximum_speed_excess_kmh=0.0,
        harsh_braking_count=0,
        aggressive_throttle_event_count=0,
        aggressive_throttle_duration_seconds=0.0,
        high_rpm_event_count=0,
        high_rpm_duration_seconds=0.0,
        severe_event_count=0,
        moderate_event_count=0,
        minor_event_count=0,
        overall_severity="none",
    )


def _make_runner(vehicle_id, trip_id, driver_id, route_id, fuel_level, distance_km):
    vehicle = Vehicle(
        vehicle_id=vehicle_id,
        make="Ford",
        model="Transit",
        year=2023,
        odometer_km=1000.0,
        fuel_level_percent=fuel_level,
    )
    driver = Driver(
        driver_id=driver_id,
        name="Test Driver",
        behavior_profile=BehaviorProfile.CAUTIOUS,
    )
    route = Route(
        route_id=route_id,
        origin="Warehouse",
        destination="Customer A",
        distance_km=distance_km,
        route_type=RouteType.URBAN,
        speed_limit_kmh=60.0,
    )
    trip = Trip(
        trip_id=trip_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        route_id=route_id,
        status=TripStatus.COMPLETED,
        started_at=datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 7, 10, 6, tzinfo=timezone.utc),
        distance_travelled_km=distance_km,
        maximum_speed_kmh=62.5,
    )
    return SimpleNamespace(
        vehicle=vehicle,
        driver=driver,
        route=route,
        trip=trip,
    )


class _StubFleet:
    """Fleet stand-in that exposes runners but reports no active runners.

    This lets ``DriveVitalsRuntime.run()`` register the trip-completion
    callback and return immediately without entering the tick loop.
    """

    def __init__(self, runners):
        self._runners = runners

    def start_all(self, now=None):
        pass

    def active_runners(self):
        return []

    def tick_all(self, now=None):
        return []


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


def test_trip_completion_callback_accepts_five_arguments():
    """The registered completion callback must handle the 5-arg contract.

    Regression: before the fix the registered ``_persist_trip_completion``
    took four arguments and the first completion raised ``TypeError``.
    """

    async def _scenario():
        persistence = _StubPersistence()
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=persistence,
        )

        runner1 = _make_runner(
            "V-1", "T-1", "D-1", "R-1", fuel_level=90.0, distance_km=5.0
        )
        runner2 = _make_runner(
            "V-2", "T-2", "D-2", "R-2", fuel_level=80.0, distance_km=12.0
        )
        runtime._fleet = _StubFleet([runner1, runner2])

        recorded = []

        def dashboard_callback(
            summary, context, runtime_state, all_events, trip
        ):
            recorded.append((summary, context, runtime_state, all_events, trip))

        runtime.set_trip_flush_callback(dashboard_callback)

        await runtime.run()

        # run() must have swapped in the persistence completion callback.
        assert runtime._trip_flush_callback is not dashboard_callback
        assert len(persistence.create_trip_calls) == 2

        # Simulate fuel consumed during the trips so the fuel math is
        # exercised (initial level captured by run(), final level lowered).
        runner1.vehicle.fuel_level_percent = 86.5
        runner2.vehicle.fuel_level_percent = 78.2

        context = AnalyticsContext(
            vehicle_id="V-1",
            driver_id="D-1",
            trip_id="T-1",
            route_id="R-1",
            route_type="urban",
            speed_limit_kmh=60.0,
            vehicle_make="Ford",
            vehicle_model="Transit",
            vehicle_year=2023,
        )
        state = RuntimeState()

        runtime._trip_flush_callback(
            _make_summary("V-1", "T-1", "D-1", 5.0),
            context,
            state,
            [],
            runner1.trip,
        )
        runtime._trip_flush_callback(
            _make_summary("V-2", "T-2", "D-2", 12.0),
            context,
            state,
            [],
            runner2.trip,
        )
        # Vehicle not found in the fleet: defaults path exercised.
        runtime._trip_flush_callback(
            _make_summary("V-999", "T-999", "D-999", 1.0),
            context,
            state,
            [],
            None,
        )

        await _drain_pending_tasks()

        # complete_trip was scheduled for every completion.
        assert sorted(
            c["trip_id"] for c in persistence.complete_trip_calls
        ) == ["T-1", "T-2", "T-999"]

        # Dashboard callback received the 5-arg contract with the Trip object.
        assert len(recorded) == 3
        assert [entry[4].trip_id for entry in recorded[:2]] == ["T-1", "T-2"]
        assert recorded[2][4] is None

        # Derived trip values are computed correctly.
        t1 = next(
            c for c in persistence.complete_trip_calls if c["trip_id"] == "T-1"
        )
        assert t1["duration_seconds"] == 360
        assert t1["fuel_used_liters"] == 2.1
        assert t1["maximum_speed_kmh"] == 62.5

    asyncio.run(_scenario())


def test_run_survives_multiple_trip_completions():
    """The full run() loop processes several completions without dying."""

    async def _scenario():
        persistence = _StubPersistence()
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=persistence,
        )

        # Analytics contexts required by the analytics engine for each vehicle.
        runtime._context_store.register(
            AnalyticsContext(
                vehicle_id="V-1",
                driver_id="D-1",
                trip_id="T-1",
                route_id="R-1",
                route_type="urban",
                speed_limit_kmh=60.0,
                vehicle_make="Ford",
                vehicle_model="Transit",
                vehicle_year=2023,
            )
        )
        runtime._context_store.register(
            AnalyticsContext(
                vehicle_id="V-2",
                driver_id="D-2",
                trip_id="T-2",
                route_id="R-2",
                route_type="urban",
                speed_limit_kmh=60.0,
                vehicle_make="Toyota",
                vehicle_model="Tacoma",
                vehicle_year=2023,
            )
        )

        # A real fleet with two short routes so both trips complete quickly.
        fleet = FleetRunner(tick_seconds=1.0)
        trips = []
        specs = [
            ("V-1", "D-1", "R-1", "T-1", 90.0, 0.1),
            ("V-2", "D-2", "R-2", "T-2", 80.0, 0.2),
        ]
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
        runtime._fleet = fleet

        completed_trips = []

        def dashboard_callback(
            summary, context, runtime_state, all_events, trip
        ):
            completed_trips.append(trip)

        runtime.set_trip_flush_callback(dashboard_callback)

        # Run the real loop quickly (no real sleep between ticks) while still
        # yielding so asyncio.ensure_future tasks (complete_trip, ...) run.
        real_sleep = asyncio.sleep

        async def fast_sleep(delay):
            await real_sleep(0)

        asyncio.sleep = fast_sleep
        try:
            await runtime.run()
        finally:
            asyncio.sleep = real_sleep

        await _drain_pending_tasks()

        # Both trips transitioned in_progress -> completed and the loop exited.
        assert [t.status for t in trips] == [
            TripStatus.COMPLETED,
            TripStatus.COMPLETED,
        ]
        assert all(t.completed_at is not None for t in trips)
        assert fleet.active_runners() == []

        # Dashboard callback fired once per completion with the trip object.
        assert sorted(t.trip_id for t in completed_trips) == ["T-1", "T-2"]

        # complete_trip was persisted for every completed trip, so the number
        # of completed trips equals the number of active vehicles (never more).
        assert sorted(
            c["trip_id"] for c in persistence.complete_trip_calls
        ) == ["T-1", "T-2"]
        assert len(persistence.complete_trip_calls) == len(trips)

    asyncio.run(_scenario())
