"""
Integration test for the brake telemetry unit contract.

Brake pressure is a raw 0.0-1.0 fraction in the runtime telemetry stream
and the internal analytics state. The canonical persistence/API unit is a
0-100 percentage stored in ``telemetry_samples.brake_percent``.

    TelemetrySample.brake_pressure (0.0-1.0) ──► brake_percent (0-100)
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


async def _scenario() -> None:
    await init_db()

    svc = PersistenceService()

    suffix = uuid4().hex[:8]
    vehicle_id = f"v-{suffix}"
    driver_id = f"d-{suffix}"
    route_id = f"r-{suffix}"
    trip_id = f"t-{suffix}"

    await _cleanup(vehicle_id, driver_id, route_id)

    try:
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
        await svc.create_trip(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            start_time=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        )

        # Full braking in the runtime stream (1.0) must persist as 100%.
        await svc.persist_telemetry(
            TelemetrySample(
                timestamp=datetime(2026, 1, 1, 8, 5, 0, tzinfo=timezone.utc),
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                trip_id=trip_id,
                speed_kmh=55.0,
                rpm=2400.0,
                throttle_position_percent=35.0,
                brake_pressure=1.0,
                coolant_temperature_c=95.0,
                engine_load_percent=60.0,
                fuel_rate_lph=8.0,
                fuel_level_percent=40.0,
                odometer_km=50010.0,
            )
        )

        # No braking (0.0) must persist as 0%.
        await svc.persist_telemetry(
            TelemetrySample(
                timestamp=datetime(2026, 1, 1, 8, 6, 0, tzinfo=timezone.utc),
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                trip_id=trip_id,
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

        # A fractional reading scales to the percent unit.
        await svc.persist_telemetry(
            TelemetrySample(
                timestamp=datetime(2026, 1, 1, 8, 7, 0, tzinfo=timezone.utc),
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                trip_id=trip_id,
                speed_kmh=55.0,
                rpm=2400.0,
                throttle_position_percent=35.0,
                brake_pressure=0.42,
                coolant_temperature_c=95.0,
                engine_load_percent=60.0,
                fuel_rate_lph=8.0,
                fuel_level_percent=40.0,
                odometer_km=50010.0,
            )
        )

        async with async_session_factory() as session:
            result = await session.execute(
                select(DBTelemetrySample.brake_percent)
                .where(DBTelemetrySample.trip_id == trip_id)
                .order_by(DBTelemetrySample.timestamp)
            )
            persisted = list(result.scalars())

        assert persisted == [100.0, 0.0, 42.0]

        # The frontend harsh-braking threshold runs on the percent scale
        # (> 70): full braking (100) exceeds it, a 42% reading does not.
        assert persisted[0] > 70
        assert persisted[2] <= 70
    finally:
        await _cleanup(vehicle_id, driver_id, route_id)
        await close_db()


class TestTelemetryBrakePercent:
    async def test_brake_pressure_is_persisted_as_percent(self) -> None:
        await _scenario()
