"""Backend analytics API tests.

Uses httpx + pytest-asyncio to test the analytics endpoints against the
test database.  The test database is isolated from development via
conftest.py (POSTGRES_DB = drivevitals_test).
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.base import Base


def _dsn() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD environment variable is not set. "
            "Copy .env.example to .env and configure your database credentials."
        )
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "drivevitals_test")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


async def _create_test_engine():
    eng = create_async_engine(_dsn(), echo=False, pool_size=5)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return eng


async def _seed_data(eng):
    async with eng.begin() as conn:
        for table in [
            "behaviour_events", "telemetry_samples", "alerts",
            "maintenance_records", "driver_statistics", "vehicle_health",
            "vehicle_statistics", "trips", "drivers", "vehicles", "routes",
        ]:
            await conn.execute(text(f"TRUNCATE {table} CASCADE"))

        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        for vid in ["V-101", "V-102", "V-103"]:
            await conn.execute(text(
                "INSERT INTO vehicles (vehicle_id, registration_number, vin, manufacturer, model, year, fuel_type, status, "
                "fuel_efficiency_factor, acceleration_response, tank_capacity_liters) "
                "VALUES (:vid, :reg, :vin, 'Toyota', 'Hilux', 2023, 'diesel', 'active', 1.0, 1.0, 60.0)"
            ), {"vid": vid, "reg": f"ABC-{vid[-3:]}", "vin": f"1HGBH41JXMN{vid[-3:]}000"})

        for did in ["D-01", "D-02", "D-03"]:
            await conn.execute(text(
                "INSERT INTO drivers (driver_id, first_name, last_name, license_number, employment_status, behavior_profile) "
                "VALUES (:did, 'Test', :name, :lic, 'active', 'standard')"
            ), {"did": did, "name": f"Driver{did[-2:]}", "lic": f"LIC-{did}"})

        await conn.execute(text(
            "INSERT INTO routes (route_id, name, route_type, origin, destination, estimated_distance_km, speed_limit_kmh, is_active) "
            "VALUES ('R-001', 'Urban Route', 'urban', 'A', 'B', 10.0, 60.0, true)"
        ))

        for i in range(5):
            start = week_ago + timedelta(days=i, hours=8)
            end = start + timedelta(hours=1)
            await conn.execute(text(
                "INSERT INTO trips (trip_id, vehicle_id, driver_id, route_id, start_time, end_time, "
                "distance_km, duration_seconds, fuel_used_liters, average_speed_kmh, trip_score, status) "
                "VALUES (:tid, :vid, :did, 'R-001', :start, :end, 10.0, 3600, 0.7, 10.0, 80.0, 'completed')"
            ), {"tid": f"TRIP-{i:03d}", "vid": "V-101", "did": "D-01", "start": start, "end": end})

        await conn.execute(text(
            "INSERT INTO trips (trip_id, vehicle_id, driver_id, route_id, start_time, status) "
            "VALUES ('TRIP-ABORT', 'V-102', 'D-02', 'R-001', :start, 'aborted')"
        ), {"start": week_ago})

        for i in range(10):
            await conn.execute(text(
                "INSERT INTO behaviour_events (event_id, trip_id, vehicle_id, driver_id, event_type, severity, "
                "started_at, ended_at, duration_seconds, distance_km, maximum_value, average_value) "
                "VALUES (:eid, 'TRIP-000', 'V-101', 'D-01', 'harsh_braking', 'minor', :start, :end, 2.0, 0.1, 0.5, 0.3)"
            ), {"eid": f"evt-{i:03d}", "start": week_ago + timedelta(hours=i), "end": week_ago + timedelta(hours=i, seconds=2)})

        for vid in ["V-101", "V-102", "V-103"]:
            await conn.execute(text(
                "INSERT INTO vehicle_health (vehicle_id, overall_health_score, engine_health, brake_health, "
                "transmission_health, cooling_health, fuel_system_health, last_updated) "
                "VALUES (:vid, 95.0, 93.0, 96.0, 94.0, 97.0, 95.0, :now)"
            ), {"vid": vid, "now": now})

        for did in ["D-01", "D-02", "D-03"]:
            await conn.execute(text(
                "INSERT INTO driver_statistics (driver_id, total_trips, total_distance_km, total_driving_time_seconds, "
                "average_trip_score, fuel_efficiency, speeding_events, harsh_braking_events, aggressive_throttle_events, "
                "high_rpm_events, safety_score, aggression_score, efficiency_score, last_updated) "
                "VALUES (:did, 5, 50.0, 18000, 80.0, 14.3, 0, 10, 5, 2, 85.0, 15.0, 90.0, :now)"
            ), {"did": did, "now": now})


@pytest_asyncio.fixture
async def client_and_seed():
    """Per-test fixture: creates engine, seeds data, overrides app dependency, yields client."""
    from backend.api.main import app
    from backend.db.session import get_session

    eng = await _create_test_engine()
    await _seed_data(eng)

    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    async def _override_session():
        async with session_factory() as session:
            yield session

    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    await eng.dispose()


@pytest.mark.asyncio
async def test_summary_returns_kpis(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "kpis" in data
    assert len(data["kpis"]) == 5
    labels = [k["label"] for k in data["kpis"]]
    assert "Safety Score" in labels
    assert "Completed Trips" in labels
    assert "Fleet Fuel Efficiency" in labels
    assert "Safety Events" in labels
    assert "Vehicle Health" in labels


@pytest.mark.asyncio
async def test_summary_range_filter(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/summary", params={"range": "last_7_days"})
    assert resp.status_code == 200
    data = resp.json()
    assert "period_start" in data
    assert "previous_start" in data


@pytest.mark.asyncio
async def test_fleet_trend(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/fleet-trend")
    assert resp.status_code == 200
    data = resp.json()
    assert "safety_score_trend" in data
    assert "event_rate_trend" in data
    assert "fuel_efficiency_trend" in data
    assert "trip_count_trend" in data


@pytest.mark.asyncio
async def test_driver_ranking(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/drivers")
    assert resp.status_code == 200
    data = resp.json()
    assert "drivers" in data
    assert len(data["drivers"]) >= 1
    driver = data["drivers"][0]
    assert "driver_id" in driver
    assert "driver_name" in driver
    assert "safety_score" in driver
    assert "completed_trips" in driver


@pytest.mark.asyncio
async def test_driver_trend(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/drivers/D-01/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert data["driver_id"] == "D-01"
    assert "observations" in data
    assert len(data["observations"]) >= 1


@pytest.mark.asyncio
async def test_vehicle_analytics(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/vehicles")
    assert resp.status_code == 200
    data = resp.json()
    assert "vehicles" in data
    assert len(data["vehicles"]) >= 1
    v = data["vehicles"][0]
    assert "vehicle_id" in v
    assert "health_score" in v
    assert "completed_trips" in v


@pytest.mark.asyncio
async def test_trip_analytics(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/trips")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_trips"] >= 1
    assert data["aborted_trips"] >= 1
    assert data["total_distance_km"] is not None


@pytest.mark.asyncio
async def test_trip_analytics_driver_filter(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/trips", params={"driver_id": "D-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_trips"] >= 1


@pytest.mark.asyncio
async def test_event_breakdown(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/events")
    assert resp.status_code == 200
    data = resp.json()
    assert "breakdown" in data
    assert data["total_events"] >= 1
    assert len(data["breakdown"]) >= 1


@pytest.mark.asyncio
async def test_event_trend(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/events/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert "trend" in data


@pytest.mark.asyncio
async def test_safety_distribution(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/safety-distribution")
    assert resp.status_code == 200
    data = resp.json()
    assert "buckets" in data
    assert "total_drivers" in data


@pytest.mark.asyncio
async def test_insights(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "insights" in data


@pytest.mark.asyncio
async def test_summary_with_driver_filter(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/summary", params={"driver_id": "D-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["kpis"]) == 5


@pytest.mark.asyncio
async def test_summary_with_vehicle_filter(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/summary", params={"vehicle_id": "V-101"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["kpis"]) == 5


@pytest.mark.asyncio
async def test_summary_empty_range(client_and_seed):
    resp = await client_and_seed.get("/api/v1/analytics/summary", params={
        "range": "custom",
        "custom_start": "2020-01-01",
        "custom_end": "2020-01-02",
    })
    assert resp.status_code == 200
    data = resp.json()
    for kpi in data["kpis"]:
        assert kpi["data_quality"] in ("valid", "insufficient", "no_data")
