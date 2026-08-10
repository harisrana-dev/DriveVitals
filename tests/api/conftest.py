import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.api.v1 import api_router
from backend.db.base import Base
from backend.db.models import (
    Alert,
    BehaviourEvent,
    Driver,
    DriverStatistics,
    MaintenanceRecord,
    Route,
    TelemetrySample,
    Trip,
    Vehicle,
    VehicleHealth,
)
from backend.db.session import get_session


def _dsn() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "drivevitals123")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "drivevitals_test")
    if not db.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run the API test suite against non-test database "
            f"'{db}'. Tests drop and reseed their database, so POSTGRES_DB "
            f"must point at a dedicated '*_test' database."
        )
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


test_engine = create_async_engine(_dsn(), poolclass=NullPool)
test_session_factory = async_sessionmaker(
    test_engine,
    expire_on_commit=False,
)


async def _reset_database() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def _seed() -> dict[str, str]:
    ids = {
        "vehicle1": "v-1",
        "vehicle2": "v-2",
        "vehicle3": "v-3",
        "vehicle4": "v-4",
        "vehicle5": "v-5",
        "driver1": "d-1",
        "driver2": "d-2",
        "driver3": "d-3",
        "route1": "r-1",
        "route2": "r-2",
        "route3": "r-3",
        "trip1": "t-1",
        "trip2": "t-2",
        "trip3": "t-3",
        "trip4": "t-4",
        "trip5": "t-5",
    }

    async with test_session_factory() as session:
        vehicles = [
            Vehicle(
                vehicle_id="v-1",
                registration_number="REG-1",
                vin="VIN-1",
                manufacturer="Test",
                model="Transit",
                year=2024,
                fuel_type="diesel",
                status="active",
            ),
            Vehicle(
                vehicle_id="v-2",
                registration_number="REG-2",
                vin="VIN-2",
                manufacturer="Test",
                model="Scania",
                year=2023,
                fuel_type="diesel",
                status="active",
            ),
            Vehicle(
                vehicle_id="v-3",
                registration_number="REG-3",
                vin="VIN-3",
                manufacturer="Test",
                model="Volvo",
                year=2022,
                fuel_type="diesel",
                status="active",
            ),
            Vehicle(
                vehicle_id="v-4",
                registration_number="REG-4",
                vin="VIN-4",
                manufacturer="Test",
                model="MAN",
                year=2021,
                fuel_type="gasoline",
                status="active",
            ),
            Vehicle(
                vehicle_id="v-5",
                registration_number="REG-5",
                vin="VIN-5",
                manufacturer="Test",
                model="Iveco",
                year=2020,
                fuel_type="gasoline",
                status="maintenance",
            ),
        ]
        drivers = [
            Driver(
                driver_id="d-1",
                first_name="Alice",
                last_name="Smith",
                license_number="LIC-1",
                employment_status="active",
            ),
            Driver(
                driver_id="d-2",
                first_name="Bob",
                last_name="Jones",
                license_number="LIC-2",
                employment_status="active",
            ),
            Driver(
                driver_id="d-3",
                first_name="Carol",
                last_name="Lee",
                license_number="LIC-3",
                employment_status="inactive",
            ),
        ]
        routes = [
            Route(
                route_id="r-1",
                name="Warehouse to Customer A",
                route_type="urban",
                origin="Warehouse",
                destination="Customer A",
                estimated_distance_km=12.5,
            ),
            Route(
                route_id="r-2",
                name="Depot to Customer B",
                route_type="highway",
                origin="Depot",
                destination="Customer B",
                estimated_distance_km=45.0,
            ),
            Route(
                route_id="r-3",
                name="Terminal to Customer C",
                route_type="urban",
                origin="Terminal",
                destination="Customer C",
                estimated_distance_km=8.0,
            ),
        ]
        session.add_all(vehicles)
        session.add_all(drivers)
        session.add_all(routes)
        await session.flush()

        trips = [
            Trip(
                trip_id="t-1",
                vehicle_id="v-1",
                driver_id="d-1",
                route_id="r-1",
                start_time=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                distance_km=12.5,
                duration_seconds=3600,
                fuel_used_liters=2.5,
                average_speed_kmh=12.5,
                maximum_speed_kmh=55.0,
                trip_score=85.0,
                status="completed",
            ),
            Trip(
                trip_id="t-2",
                vehicle_id="v-1",
                driver_id="d-2",
                route_id="r-2",
                start_time=datetime(2026, 1, 2, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 2, 9, 30, 0, tzinfo=timezone.utc),
                distance_km=45.0,
                duration_seconds=5400,
                fuel_used_liters=9.0,
                average_speed_kmh=30.0,
                maximum_speed_kmh=88.0,
                trip_score=72.0,
                status="completed",
            ),
            Trip(
                trip_id="t-3",
                vehicle_id="v-2",
                driver_id="d-1",
                route_id="r-1",
                start_time=datetime(2026, 1, 3, 8, 0, 0, tzinfo=timezone.utc),
                end_time=None,
                distance_km=None,
                duration_seconds=None,
                fuel_used_liters=None,
                average_speed_kmh=None,
                maximum_speed_kmh=None,
                trip_score=None,
                status="in_progress",
            ),
            Trip(
                trip_id="t-4",
                vehicle_id="v-2",
                driver_id="d-2",
                route_id="r-3",
                start_time=datetime(2026, 1, 4, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 4, 8, 45, 0, tzinfo=timezone.utc),
                distance_km=8.0,
                duration_seconds=2700,
                fuel_used_liters=1.6,
                average_speed_kmh=10.0,
                maximum_speed_kmh=50.0,
                trip_score=90.0,
                status="completed",
            ),
            Trip(
                trip_id="t-5",
                vehicle_id="v-3",
                driver_id="d-3",
                route_id="r-2",
                start_time=datetime(2026, 1, 5, 8, 0, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 1, 5, 8, 30, 0, tzinfo=timezone.utc),
                distance_km=None,
                duration_seconds=None,
                fuel_used_liters=None,
                average_speed_kmh=None,
                maximum_speed_kmh=None,
                trip_score=None,
                status="aborted",
            ),
        ]
        session.add_all(trips)
        await session.flush()

        session.add_all(
            [
                BehaviourEvent(
                    event_id="be-1",
                    trip_id="t-1",
                    vehicle_id="v-1",
                    driver_id="d-1",
                    event_type="speeding",
                    severity="moderate",
                    started_at=datetime(2026, 1, 1, 8, 20, 0, tzinfo=timezone.utc),
                    ended_at=datetime(2026, 1, 1, 8, 20, 20, tzinfo=timezone.utc),
                    duration_seconds=20.0,
                    distance_km=0.4,
                    maximum_value=75.0,
                    average_value=68.0,
                ),
                BehaviourEvent(
                    event_id="be-2",
                    trip_id="t-1",
                    vehicle_id="v-1",
                    driver_id="d-1",
                    event_type="harsh_braking",
                    severity="moderate",
                    started_at=datetime(2026, 1, 1, 8, 40, 0, tzinfo=timezone.utc),
                    ended_at=datetime(2026, 1, 1, 8, 40, 3, tzinfo=timezone.utc),
                    duration_seconds=3.0,
                    distance_km=0.05,
                    maximum_value=0.9,
                    average_value=0.85,
                ),
                BehaviourEvent(
                    event_id="be-3",
                    trip_id="t-1",
                    vehicle_id="v-1",
                    driver_id="d-1",
                    event_type="aggressive_throttle",
                    severity="minor",
                    started_at=datetime(2026, 1, 1, 8, 50, 0, tzinfo=timezone.utc),
                    ended_at=datetime(2026, 1, 1, 8, 50, 10, tzinfo=timezone.utc),
                    duration_seconds=10.0,
                    distance_km=0.2,
                    maximum_value=95.0,
                    average_value=90.0,
                ),
            ]
        )
        await session.flush()

        samples = [
            TelemetrySample(
                sample_id=str(uuid4()),
                trip_id="t-1",
                vehicle_id="v-1",
                timestamp=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
                speed_kmh=40.0,
                rpm=2200.0,
                engine_load_percent=55.0,
                throttle_percent=30.0,
                brake_percent=0.0,
                fuel_rate_lph=6.0,
                fuel_level_percent=80.0,
                coolant_temperature_c=88.0,
                odometer_km=1000.0,
            ),
            TelemetrySample(
                sample_id=str(uuid4()),
                trip_id="t-1",
                vehicle_id="v-1",
                timestamp=datetime(2026, 1, 1, 8, 30, 0, tzinfo=timezone.utc),
                speed_kmh=55.0,
                rpm=2800.0,
                engine_load_percent=70.0,
                throttle_percent=45.0,
                brake_percent=5.0,
                fuel_rate_lph=8.0,
                fuel_level_percent=75.0,
                coolant_temperature_c=90.0,
                odometer_km=1005.0,
            ),
            TelemetrySample(
                sample_id=str(uuid4()),
                trip_id="t-1",
                vehicle_id="v-1",
                timestamp=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                speed_kmh=20.0,
                rpm=1500.0,
                engine_load_percent=30.0,
                throttle_percent=10.0,
                brake_percent=20.0,
                fuel_rate_lph=3.0,
                fuel_level_percent=73.0,
                coolant_temperature_c=87.0,
                odometer_km=1012.5,
            ),
            TelemetrySample(
                sample_id=str(uuid4()),
                trip_id="t-3",
                vehicle_id="v-2",
                timestamp=datetime(2026, 1, 3, 8, 0, 0, tzinfo=timezone.utc),
                speed_kmh=30.0,
                rpm=1800.0,
                engine_load_percent=40.0,
                throttle_percent=20.0,
                brake_percent=0.0,
                fuel_rate_lph=4.0,
                fuel_level_percent=90.0,
                coolant_temperature_c=82.0,
                odometer_km=2000.0,
            ),
            TelemetrySample(
                sample_id=str(uuid4()),
                trip_id="t-3",
                vehicle_id="v-2",
                timestamp=datetime(2026, 1, 3, 8, 30, 0, tzinfo=timezone.utc),
                speed_kmh=50.0,
                rpm=2400.0,
                engine_load_percent=60.0,
                throttle_percent=35.0,
                brake_percent=10.0,
                fuel_rate_lph=7.0,
                fuel_level_percent=88.0,
                coolant_temperature_c=85.0,
                odometer_km=2005.0,
            ),
        ]
        session.add_all(samples)

        session.add_all(
            [
                VehicleHealth(
                    vehicle_id="v-1",
                    overall_health_score=88.5,
                    engine_health=90.0,
                    brake_health=85.0,
                    transmission_health=92.0,
                    cooling_health=88.0,
                    fuel_system_health=80.0,
                    last_updated=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                ),
                DriverStatistics(
                    driver_id="d-1",
                    total_trips=3,
                    total_distance_km=75.5,
                    total_driving_time_seconds=10000,
                    average_trip_score=82.0,
                    fuel_efficiency=8.5,
                    speeding_events=1,
                    harsh_braking_events=2,
                    aggressive_throttle_events=1,
                    high_rpm_events=0,
                    safety_score=84.0,
                    aggression_score=30.0,
                    efficiency_score=78.0,
                    last_updated=datetime(2026, 1, 3, 9, 0, 0, tzinfo=timezone.utc),
                ),
            ]
        )

        session.add_all(
            [
                MaintenanceRecord(
                    maintenance_id=str(uuid4()),
                    vehicle_id="v-1",
                    maintenance_type="engine",
                    priority="high",
                    status="pending",
                    due_odometer_km=100000.0,
                    completed_odometer_km=None,
                    created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                    completed_at=None,
                ),
                MaintenanceRecord(
                    maintenance_id=str(uuid4()),
                    vehicle_id="v-1",
                    maintenance_type="brakes",
                    priority="medium",
                    status="pending",
                    due_odometer_km=90000.0,
                    completed_odometer_km=None,
                    created_at=datetime(2026, 1, 2, 9, 0, 0, tzinfo=timezone.utc),
                    completed_at=None,
                ),
            ]
        )

        session.add_all(
            [
                Alert(
                    alert_id="a-1",
                    vehicle_id="v-1",
                    driver_id="d-1",
                    trip_id="t-1",
                    alert_type="health",
                    severity="critical",
                    status="active",
                    acknowledged=False,
                    created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
                    resolved_at=None,
                ),
                Alert(
                    alert_id="a-2",
                    vehicle_id="v-1",
                    driver_id="d-2",
                    trip_id="t-2",
                    alert_type="maintenance",
                    severity="high",
                    status="active",
                    acknowledged=True,
                    created_at=datetime(2026, 1, 2, 9, 0, 0, tzinfo=timezone.utc),
                    resolved_at=None,
                ),
                Alert(
                    alert_id="a-3",
                    vehicle_id="v-1",
                    driver_id="d-1",
                    trip_id="t-1",
                    alert_type="telemetry",
                    severity="medium",
                    status="resolved",
                    acknowledged=True,
                    created_at=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                    resolved_at=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                ),
            ]
        )

        await session.commit()

    return ids


async def _override_get_session():
    async with test_session_factory() as session:
        yield session


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[get_session] = _override_get_session
    return app


@pytest.fixture
async def ids() -> dict[str, str]:
    await _reset_database()
    return await _seed()


@pytest.fixture
async def client(ids: dict[str, str]) -> AsyncClient:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def empty_client() -> AsyncClient:
    await _reset_database()
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
