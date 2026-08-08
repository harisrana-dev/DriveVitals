"""
Stale in_progress-trip handling at runtime startup.

Every runtime session creates one trip per vehicle. Trips left
``in_progress`` in the database by a previous session must be terminated
(``aborted``) when a new session starts, so orphan trips are never reported
as active. These tests verify:

  * ``run()`` aborts stale trips before creating the current session's trips,
  * ``run()`` tolerates a ``None`` persistence service,
  * the domain ``Trip.abort`` transition terminates without fabricating
    completion metrics,
  * during a full run the number of concurrent ``in_progress`` trips never
    exceeds the number of vehicles.
"""

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from backend.application.runtime import DriveVitalsRuntime
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner


class _RecordingPersistence:
    """Records persistence calls in order so startup sequencing can be
    asserted."""

    def __init__(self):
        self.calls = []

    async def abort_stale_trips(self, **kwargs):
        self.calls.append(("abort_stale_trips", kwargs))

    async def create_trip(self, **kwargs):
        self.calls.append(("create_trip", kwargs))

    async def complete_trip(self, **kwargs):
        self.calls.append(("complete_trip", kwargs))

    async def _noop(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self._noop


class _LoggingPersistence(_RecordingPersistence):
    """Tracks the concurrent in_progress trip count as events replay."""

    def __init__(self):
        super().__init__()
        self.peak_in_progress = 0
        self._active = 0

    async def create_trip(self, **kwargs):
        await super().create_trip(**kwargs)
        self._active += 1
        self.peak_in_progress = max(self.peak_in_progress, self._active)

    async def complete_trip(self, **kwargs):
        await super().complete_trip(**kwargs)
        self._active -= 1


class _StubFleet:
    """Fleet stand-in exposing runners but reporting no active runners, so
    ``run()`` returns immediately after setup."""

    def __init__(self, runners):
        self._runners = runners

    def start_all(self, now=None):
        pass

    def active_runners(self):
        return []

    def tick_all(self, now=None):
        return []


def _make_runner(vehicle_id, trip_id):
    vehicle = Vehicle(
        vehicle_id=vehicle_id,
        make="Ford",
        model="Transit",
        year=2023,
        odometer_km=1000.0,
        fuel_level_percent=90.0,
    )
    driver = Driver(
        driver_id="D-1",
        name="Test Driver",
        behavior_profile=BehaviorProfile.CAUTIOUS,
    )
    route = Route(
        route_id="R-1",
        origin="Warehouse",
        destination="Customer A",
        distance_km=5.0,
        route_type=RouteType.URBAN,
        speed_limit_kmh=60.0,
    )
    trip = Trip(
        trip_id=trip_id,
        vehicle_id=vehicle_id,
        driver_id="D-1",
        route_id="R-1",
    )
    return SimpleNamespace(
        vehicle=vehicle,
        driver=driver,
        route=route,
        trip=trip,
    )


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


def test_abort_stale_trips_runs_before_trip_creation():
    """run() terminates trips left in_progress by a previous session before
    creating the current session's trips."""

    async def _scenario():
        persistence = _RecordingPersistence()
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=persistence,
        )
        runtime._fleet = _StubFleet([_make_runner("V-1", "T-1")])

        await runtime.run()

        kinds = [name for name, _ in persistence.calls]
        assert kinds == ["abort_stale_trips", "create_trip"]
        abort_kwargs = persistence.calls[0][1]
        assert abort_kwargs["end_time"] is not None

    asyncio.run(_scenario())


def test_run_tolerates_missing_persistence():
    """run() without a persistence service skips the stale-trip abort
    instead of raising."""

    async def _scenario():
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=None,
        )
        runtime._fleet = _StubFleet([_make_runner("V-1", "T-1")])

        await runtime.run()

    asyncio.run(_scenario())


def test_domain_trip_abort_terminates_without_fabricating_metrics():
    trip = Trip(trip_id="T-1", vehicle_id="V-1", driver_id="D-1", route_id="R-1")
    trip.start(1000.0, at=datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc))
    trip.advance(3.0)
    trip.fuel_used_liters = 0.4

    end = datetime(2026, 8, 7, 10, 5, tzinfo=timezone.utc)
    trip.abort(at=end)

    assert trip.status == TripStatus.ABORTED
    assert trip.completed_at == end
    # Metrics recorded so far are preserved; no completion metrics invented.
    assert trip.distance_travelled_km == 3.0
    assert trip.fuel_used_liters == 0.4
    assert trip.ending_odometer_km is None


def test_domain_trip_cannot_abort_after_completion():
    trip = Trip(trip_id="T-1", vehicle_id="V-1", driver_id="D-1", route_id="R-1")
    trip.start(1000.0, at=datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc))
    trip.advance(10.0)
    trip.complete(1010.0)

    try:
        trip.abort()
    except ValueError:
        pass
    else:
        raise AssertionError("abort() must refuse a completed trip")


def test_active_trips_never_exceed_vehicles():
    """During a full run the number of concurrent in_progress trips is
    bounded by the number of vehicles (one trip per vehicle, ever)."""

    async def _scenario():
        persistence = _LoggingPersistence()
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=persistence,
        )

        fleet = FleetRunner(tick_seconds=1.0)
        specs = [
            ("V-1", "D-1", "R-1", "T-1", 90.0, 0.1),
            ("V-2", "D-2", "R-2", "T-2", 80.0, 0.2),
            ("V-3", "D-3", "R-3", "T-3", 70.0, 0.3),
            ("V-4", "D-4", "R-4", "T-4", 60.0, 0.4),
            ("V-5", "D-5", "R-5", "T-5", 50.0, 0.5),
            ("V-6", "D-6", "R-6", "T-6", 40.0, 0.6),
        ]
        for vid, did, rid, tid, fuel, distance in specs:
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

        real_sleep = asyncio.sleep

        async def fast_sleep(delay):
            await real_sleep(0)

        asyncio.sleep = fast_sleep
        try:
            await runtime.run()
        finally:
            asyncio.sleep = real_sleep

        await _drain_pending_tasks()

        # Startup abort ran first, then one trip per vehicle was created.
        assert persistence.calls[0][0] == "abort_stale_trips"
        assert [n for n, _ in persistence.calls].count("create_trip") == len(specs)

        # At no point did the active in_progress set exceed the fleet size.
        assert persistence.peak_in_progress <= len(specs)

        # Every trip completed and was persisted; none remain in_progress.
        assert persistence._active == 0
        assert [n for n, _ in persistence.calls].count("complete_trip") == len(specs)

    asyncio.run(_scenario())
