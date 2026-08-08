"""
Active-trip invariant at the database layer.

At no point in the active-trip lifecycle may the number of ``in_progress``
trip rows exceed the number of active vehicles (one trip per vehicle per
session, ever). This verifies the invariant against a real database during a
full runtime session that starts with orphan rows left by a previous session:

  * orphan ``in_progress`` rows from a previous session are aborted before the
    current session's trips are created,
  * the peak concurrent ``in_progress`` count never exceeds the number of
    vehicles,
  * every current-session trip ends (``completed``), leaving zero
    ``in_progress`` rows when the session finishes.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.analytics.context.analytics_context import AnalyticsContext
from backend.application.runtime import DriveVitalsRuntime
from backend.db.models.alert import Alert as DBAlert
from backend.db.models.driver import Driver as DBDriver
from backend.db.models.driver_statistics import DriverStatistics as DBDriverStatistics
from backend.db.models.behaviour_event import BehaviourEvent as DBBehaviourEvent
from backend.db.models.maintenance_record import MaintenanceRecord as DBMaintenanceRecord
from backend.db.models.route import Route as DBRoute
from backend.db.models.telemetry_sample import TelemetrySample as DBTelemetrySample
from backend.db.models.trip import Trip as DBTrip
from backend.db.models.vehicle import Vehicle as DBVehicle
from backend.db.models.vehicle_health import VehicleHealth as DBVehicleHealth
from backend.db.persistence_service import PersistenceService
from backend.db.session import async_session_factory, close_db, init_db
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner


class _InvariantPersistence(PersistenceService):
    """Records the peak concurrent in_progress trip count as DB writes land."""

    def __init__(self):
        super().__init__()
        self.peak_in_progress = 0
        self.samples = 0

    async def create_trip(self, **kwargs):
        await super().create_trip(**kwargs)
        await self._record()

    async def complete_trip(self, **kwargs):
        await super().complete_trip(**kwargs)
        await self._record()

    async def abort_stale_trips(self, **kwargs):
        await super().abort_stale_trips(**kwargs)
        await self._record()

    async def _record(self) -> None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(DBTrip).where(
                    DBTrip.status == "in_progress"
                )
            )
            count = int(result.scalar_one())
        self.samples += 1
        self.peak_in_progress = max(self.peak_in_progress, count)


async def _count_in_progress() -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(DBTrip).where(
                DBTrip.status == "in_progress"
            )
        )
        return int(result.scalar_one())


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


async def _cleanup(ids: dict) -> None:
    vehicle_ids = list(ids["vehicle_ids"])
    async with async_session_factory() as session:
        await session.execute(
            delete(DBBehaviourEvent).where(
                DBBehaviourEvent.trip_id.in_(
                    select(DBTrip.trip_id).where(
                        DBTrip.vehicle_id.in_(vehicle_ids)
                    )
                )
            )
        )
        await session.execute(
            delete(DBAlert).where(DBAlert.vehicle_id.in_(vehicle_ids))
        )
        await session.execute(
            delete(DBDriverStatistics).where(
                DBDriverStatistics.driver_id.in_(ids["driver_ids"])
            )
        )
        await session.execute(
            delete(DBMaintenanceRecord).where(
                DBMaintenanceRecord.vehicle_id.in_(vehicle_ids)
            )
        )
        await session.execute(
            delete(DBVehicleHealth).where(
                DBVehicleHealth.vehicle_id.in_(vehicle_ids)
            )
        )
        await session.execute(
            delete(DBTelemetrySample).where(
                DBTelemetrySample.vehicle_id.in_(vehicle_ids)
            )
        )
        await session.execute(
            delete(DBTrip).where(DBTrip.vehicle_id.in_(vehicle_ids))
        )
        await session.execute(
            delete(DBRoute).where(DBRoute.route_id.in_(ids["route_ids"]))
        )
        await session.execute(
            delete(DBDriver).where(DBDriver.driver_id.in_(ids["driver_ids"]))
        )
        await session.execute(
            delete(DBVehicle).where(DBVehicle.vehicle_id.in_(vehicle_ids))
        )
        await session.commit()


async def _scenario() -> None:
    await init_db()

    svc = PersistenceService()
    invariant = _InvariantPersistence()

    suffix = uuid4().hex[:6]
    specs = [
        ("V-1", "D-1", "R-1", "T-1", 90.0, 0.1),
        ("V-2", "D-2", "R-2", "T-2", 80.0, 0.2),
        ("V-3", "D-3", "R-3", "T-3", 70.0, 0.3),
        ("V-4", "D-4", "R-4", "T-4", 60.0, 0.4),
        ("V-5", "D-5", "R-5", "T-5", 50.0, 0.5),
        ("V-6", "D-6", "R-6", "T-6", 40.0, 0.6),
    ]
    ids = {
        "vehicle_ids": [f"v{vid}-{suffix}" for vid, *_ in specs],
        "driver_ids": [f"d{did}-{suffix}" for _, did, *_ in specs],
        "route_ids": [f"r{rid}-{suffix}" for _, _, rid, *_ in specs],
    }
    trip_ids = [f"t{tid}-{suffix}" for _, _, _, tid, *_ in specs]

    await _cleanup(ids)

    try:
        # The test database may already hold in_progress rows left by other
        # sessions; treat them as orphans the startup abort must clear.
        baseline_in_progress = await _count_in_progress()

        # --------------------------------------------------------------
        # Reference data (FK parents)
        # --------------------------------------------------------------
        for vid, did, rid, _tid, fuel, _distance in specs:
            await svc.persist_vehicle(
                Vehicle(
                    vehicle_id=f"v{vid}-{suffix}",
                    make="Test",
                    model="Transit",
                    year=2024,
                    odometer_km=50000.0,
                    fuel_level_percent=fuel,
                )
            )
            await svc.persist_driver(
                Driver(driver_id=f"d{did}-{suffix}", name="Test Driver")
            )
            await svc.persist_route(
                Route(
                    route_id=f"r{rid}-{suffix}",
                    origin="Warehouse",
                    destination="Customer",
                    distance_km=10.0,
                    route_type="urban",
                    speed_limit_kmh=60.0,
                )
            )

        # --------------------------------------------------------------
        # Orphan trips left in_progress by a previous session
        # --------------------------------------------------------------
        for vid, did, rid, _tid, _fuel, _distance in specs:
            await svc.create_trip(
                trip_id=f"torphan{vid}-{suffix}",
                vehicle_id=f"v{vid}-{suffix}",
                driver_id=f"d{did}-{suffix}",
                route_id=f"r{rid}-{suffix}",
                start_time=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            )

        assert await _count_in_progress() == baseline_in_progress + len(specs)

        # --------------------------------------------------------------
        # Build the runtime with the same fleet shape
        # --------------------------------------------------------------
        runtime = DriveVitalsRuntime(
            tick_seconds=1.0,
            persistence_service=invariant,
        )

        fleet = FleetRunner(tick_seconds=1.0)
        trips = []
        for vid, did, rid, tid, fuel, distance in specs:
            runtime._context_store.register(
                AnalyticsContext(
                    vehicle_id=f"v{vid}-{suffix}",
                    driver_id=f"d{did}-{suffix}",
                    trip_id=f"t{tid}-{suffix}",
                    route_id=f"r{rid}-{suffix}",
                    route_type="urban",
                    speed_limit_kmh=60.0,
                    vehicle_make="Test",
                    vehicle_model="Transit",
                    vehicle_year=2024,
                )
            )
            vehicle = Vehicle(
                vehicle_id=f"v{vid}-{suffix}",
                make="Test",
                model="Transit",
                year=2024,
                odometer_km=50000.0,
                fuel_level_percent=fuel,
            )
            driver = Driver(
                driver_id=f"d{did}-{suffix}",
                name="Test Driver",
                behavior_profile=BehaviorProfile.CAUTIOUS,
            )
            route = Route(
                route_id=f"r{rid}-{suffix}",
                origin="Warehouse",
                destination="Customer",
                distance_km=distance,
                route_type=RouteType.URBAN,
                speed_limit_kmh=60.0,
            )
            trip = Trip(
                trip_id=f"t{tid}-{suffix}",
                vehicle_id=f"v{vid}-{suffix}",
                driver_id=f"d{did}-{suffix}",
                route_id=f"r{rid}-{suffix}",
            )
            trips.append(trip)
            fleet.add_assignment(
                assignment=Assignment(
                    assignment_id=f"A{vid}-{suffix}",
                    driver_id=f"d{did}-{suffix}",
                    vehicle_id=f"v{vid}-{suffix}",
                    route_id=f"r{rid}-{suffix}",
                ),
                vehicle=vehicle,
                driver=driver,
                route=route,
                trip=trip,
            )
        runtime._fleet = fleet

        # --------------------------------------------------------------
        # Run the full session
        # --------------------------------------------------------------
        real_sleep = asyncio.sleep

        async def fast_sleep(delay):
            await real_sleep(0)

        asyncio.sleep = fast_sleep
        try:
            await runtime.run()
        finally:
            asyncio.sleep = real_sleep

        await _drain_pending_tasks()

        # The DB was observed at every write boundary and the concurrent
        # in_progress count never exceeded the number of vehicles.
        assert invariant.samples >= len(specs)
        assert invariant.peak_in_progress <= len(specs)

        # Every current-session trip completed and every orphan (including
        # any left by other sessions in the shared test database) was aborted
        # at startup, so nothing remains in_progress.
        assert fleet.active_runners() == []
        assert await _count_in_progress() == 0

        # The orphan rows from the previous session were aborted (not left
        # in_progress, not fabricated into completed).
        async with async_session_factory() as session:
            result = await session.execute(
                select(DBTrip.status).where(
                    DBTrip.trip_id.in_(
                        [f"torphan{vid}-{suffix}" for vid, *_ in specs]
                    )
                )
            )
            assert set(result.scalars()) == {"aborted"}
    finally:
        await _cleanup(ids)
        await close_db()


class TestActiveTripInvariant:
    async def test_in_progress_never_exceeds_vehicles(self) -> None:
        await _scenario()
