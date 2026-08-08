"""
Integration tests for the stale in_progress-trip abort at runtime startup.

On startup the runtime marks every ``in_progress`` trip (necessarily left
behind by a previous session) as ``aborted`` so orphan trips are never
reported as active. This verifies the persistence side of that contract:

    stale in_progress trip ──► abort_stale_trips ──► aborted (end_time set)

  * only pre-existing in_progress rows are transitioned,
  * an end/termination timestamp is set,
  * recorded metrics are preserved (no completion metrics are fabricated),
  * telemetry history is untouched,
  * trips created after the abort (the current session) stay in_progress.
"""

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, select

# Ensure backend/ is on sys.path so backend.* resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.db.models.driver import Driver as DBDriver
from backend.db.models.route import Route as DBRoute
from backend.db.models.telemetry_sample import TelemetrySample as DBTelemetrySample
from backend.db.models.trip import Trip as DBTrip
from backend.db.models.vehicle import Vehicle as DBVehicle
from backend.db.persistence_service import PersistenceService
from backend.db.session import async_session_factory, close_db, init_db
from backend.fleet.models.driver import Driver as DomainDriver
from backend.fleet.models.route import Route as DomainRoute
from backend.fleet.models.vehicle import Vehicle as DomainVehicle
from backend.telemetry.models.telemetry_sample import TelemetrySample


async def _cleanup(vehicle_id: str, driver_id: str, route_id: str) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(DBTelemetrySample).where(
                DBTelemetrySample.vehicle_id == vehicle_id
            )
        )
        await session.execute(
            delete(DBTrip).where(DBTrip.vehicle_id == vehicle_id)
        )
        await session.execute(
            delete(DBRoute).where(DBRoute.route_id == route_id)
        )
        await session.execute(
            delete(DBDriver).where(DBDriver.driver_id == driver_id)
        )
        await session.execute(
            delete(DBVehicle).where(DBVehicle.vehicle_id == vehicle_id)
        )
        await session.commit()


async def _read_trip(trip_id: str) -> DBTrip | None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(DBTrip).where(DBTrip.trip_id == trip_id)
        )
        return result.scalar_one_or_none()


async def _count_telemetry(trip_id: str) -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(DBTelemetrySample.trip_id).where(
                DBTelemetrySample.trip_id == trip_id
            )
        )
        return len(result.all())


async def _scenario() -> None:
    await init_db()

    svc = PersistenceService()

    suffix = uuid4().hex[:8]
    vehicle_id = f"v-{suffix}"
    driver_id = f"d-{suffix}"
    route_id = f"r-{suffix}"
    stale_trip_id = f"t-stale-{suffix}"
    current_trip_id = f"t-current-{suffix}"

    await _cleanup(vehicle_id, driver_id, route_id)

    try:
        # --------------------------------------------------------------
        # Reference data (FK parents)
        # --------------------------------------------------------------
        vehicle = DomainVehicle(
            vehicle_id=vehicle_id,
            make="Test",
            model="Transit",
            year=2024,
            odometer_km=50000.0,
        )
        driver = DomainDriver(driver_id=driver_id, name="Test Driver")
        route = DomainRoute(
            route_id=route_id,
            origin="Warehouse",
            destination="Customer",
            distance_km=10.0,
            route_type="urban",
            speed_limit_kmh=60.0,
        )

        await svc.persist_vehicle(vehicle)
        await svc.persist_driver(driver)
        await svc.persist_route(route)

        # --------------------------------------------------------------
        # A trip left in_progress by a previous session
        # --------------------------------------------------------------
        await svc.create_trip(
            trip_id=stale_trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            start_time=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        )

        # Telemetry recorded during the interrupted session.
        await svc.persist_telemetry(
            TelemetrySample(
                timestamp=datetime(2026, 1, 1, 8, 5, 0, tzinfo=timezone.utc),
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                trip_id=stale_trip_id,
                speed_kmh=55.0,
                rpm=2400.0,
                throttle_position_percent=35.0,
                brake_pressure=0.0,
                coolant_temperature_c=95.0,
                engine_load_percent=60.0,
                fuel_rate_lph=8.0,
                fuel_level_percent=40.0,
                odometer_km=50010.0,
            )
        )

        stale_before = await _read_trip(stale_trip_id)
        assert stale_before is not None
        assert stale_before.status == "in_progress"

        # --------------------------------------------------------------
        # Startup abort
        # --------------------------------------------------------------
        end_time = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        aborted = await svc.abort_stale_trips(end_time=end_time)

        assert aborted >= 1

        stale_after = await _read_trip(stale_trip_id)
        assert stale_after is not None
        assert stale_after.status == "aborted"
        assert stale_after.end_time == end_time
        # No completion metrics were fabricated.
        assert stale_after.distance_km is None
        assert stale_after.duration_seconds is None
        assert stale_after.fuel_used_liters is None
        assert stale_after.trip_score is None
        # Telemetry history is preserved.
        assert await _count_telemetry(stale_trip_id) == 1

        # --------------------------------------------------------------
        # A trip created after the abort (this session) stays active
        # --------------------------------------------------------------
        await svc.create_trip(
            trip_id=current_trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            start_time=datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc),
        )

        current = await _read_trip(current_trip_id)
        assert current is not None
        assert current.status == "in_progress"

        # A later startup's abort must not touch the already-aborted stale
        # trip but must still clear the previous session's trip.
        second = await svc.abort_stale_trips(end_time=end_time)
        assert second >= 1
        assert (await _read_trip(stale_trip_id)).status == "aborted"
        assert (await _read_trip(current_trip_id)).status == "aborted"
    finally:
        await _cleanup(vehicle_id, driver_id, route_id)
        await close_db()


class TestStaleTripAbortPersistence:
    async def test_stale_in_progress_trips_are_aborted(self) -> None:
        await _scenario()
