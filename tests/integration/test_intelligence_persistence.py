"""
Integration tests for Fleet Intelligence Phase 2 persistence.

Verifies PersistenceService writes vehicle health, driver statistics,
maintenance records and fleet alerts into PostgreSQL:

    HealthSnapshot    ──► persist_vehicle_health      ──► vehicle_health
    DriverStatistics  ──► persist_driver_statistics   ──► driver_statistics
    MaintenanceRecord ──► persist_maintenance_records ──► maintenance_records
    FleetAlert        ──► persist_alerts              ──► alerts

Each flow produces its input through the real Phase 1 engine/consumer so
the test covers the full analytics-to-persistence handoff. The async test
runs under pytest-asyncio so all database work stays on a single event
loop.
"""

import os
import sys
from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import delete, select

# Ensure backend/ is on sys.path so backend.* resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.alerts.alert_engine import AlertEngine
from backend.alerts.generators import (
    HealthAlertsGenerator,
    MaintenanceAlertsGenerator,
    TelemetryAlertsGenerator,
    TripAlertsGenerator,
)
from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.driver_statistics import (
    DriverScoreCalculator,
    DriverStatisticsEngine,
)
from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.snapshot.snapshot_store import AnalyticsSnapshotStore
from backend.analytics.vehicle_health.analyzers.brake_health import (
    BrakeHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.cooling_health import (
    CoolingHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.engine_health import (
    EngineHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.fuel_system_health import (
    FuelSystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.analyzers.transmission_health import (
    TransmissionHealthAnalyzer,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.vehicle_health_engine import (
    VehicleHealthEngine,
)
from backend.application.consumers.driver_statistics_consumer import (
    DriverStatisticsConsumer,
)
from backend.application.consumers.vehicle_health_consumer import (
    VehicleHealthConsumer,
)
from backend.application.intelligence_state import IntelligenceState
from backend.db.models.alert import Alert
from backend.db.models.driver import Driver as DBDriver
from backend.db.models.driver_statistics import (
    DriverStatistics as DBDriverStatistics,
)
from backend.db.models.maintenance_record import (
    MaintenanceRecord as DBMaintenanceRecord,
)
from backend.db.models.route import Route as DBRoute
from backend.db.models.telemetry_sample import TelemetrySample as DBTelemetrySample
from backend.db.models.trip import Trip as DBTrip
from backend.db.models.vehicle import Vehicle as DBVehicle
from backend.db.models.vehicle_health import VehicleHealth
from backend.db.persistence_service import PersistenceService
from backend.db.session import async_session_factory, close_db, init_db
from backend.fleet.models.driver import Driver as DomainDriver
from backend.fleet.models.route import Route as DomainRoute
from backend.fleet.models.trip import Trip as DomainTrip
from backend.fleet.models.vehicle import Vehicle as DomainVehicle
from backend.maintenance.estimators import (
    BrakeEstimator,
    CoolingEstimator,
    EngineEstimator,
    FuelSystemEstimator,
    TransmissionEstimator,
)
from backend.maintenance.maintenance_service import MaintenanceService
from backend.pipeline.telemetry_pipeline import TelemetryPipeline
from backend.telemetry.models.telemetry_sample import TelemetrySample


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample(
    vehicle_id: str,
    driver_id: str,
    trip_id: str,
    timestamp: datetime | None = None,
) -> TelemetrySample:
    return TelemetrySample(
        timestamp=timestamp or datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        speed_kmh=55.0,
        rpm=6800.0,
        throttle_position_percent=35.0,
        brake_pressure=0.0,
        coolant_temperature_c=115.0,
        engine_load_percent=95.0,
        fuel_rate_lph=8.0,
        fuel_level_percent=5.0,
        odometer_km=50000.0,
    )


def _make_analytics_snapshot(
    vehicle_id: str,
    driver_id: str,
    trip_id: str,
    sample: TelemetrySample,
) -> AnalyticsSnapshot:
    return AnalyticsSnapshot(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        timestamp=sample.timestamp,
        telemetry=sample,
        behaviour=DriverBehaviourAnalysis(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
            speeding=True,
            speed_excess_kmh=15.0,
            harsh_braking=True,
            aggressive_throttle=True,
            high_rpm=True,
            severity="severe",
            odometer_km=sample.odometer_km,
        ),
        completed_events=(),
        active_event_types=(),
    )


def _make_event(
    vehicle_id: str,
    driver_id: str,
    trip_id: str,
    event_type: str,
) -> BehaviourEvent:
    started = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    return BehaviourEvent(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        event_type=event_type,
        started_at=started,
        ended_at=started,
        duration_seconds=5.0,
        distance_km=0.1,
        severity="severe",
    )


async def _cleanup(
    vehicle_id: str,
    driver_id: str,
    route_id: str,
    trip_id: str,
) -> None:
    async with async_session_factory() as session:
        await session.execute(
            delete(Alert).where(Alert.vehicle_id == vehicle_id)
        )
        await session.execute(
            delete(DBMaintenanceRecord).where(
                DBMaintenanceRecord.vehicle_id == vehicle_id
            )
        )
        await session.execute(
            delete(DBDriverStatistics).where(
                DBDriverStatistics.driver_id == driver_id
            )
        )
        await session.execute(
            delete(VehicleHealth).where(
                VehicleHealth.vehicle_id == vehicle_id
            )
        )
        await session.execute(
            delete(DBTelemetrySample).where(
                DBTelemetrySample.vehicle_id == vehicle_id
            )
        )
        await session.execute(
            delete(DBTrip).where(DBTrip.trip_id == trip_id)
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


async def _read_vehicle_health(vehicle_id: str) -> VehicleHealth:
    async with async_session_factory() as session:
        result = await session.execute(
            select(VehicleHealth).where(VehicleHealth.vehicle_id == vehicle_id)
        )
        return result.scalar_one()


async def _read_driver_statistics(driver_id: str) -> DBDriverStatistics:
    async with async_session_factory() as session:
        result = await session.execute(
            select(DBDriverStatistics).where(
                DBDriverStatistics.driver_id == driver_id
            )
        )
        return result.scalar_one()


async def _read_maintenance_records(vehicle_id: str) -> list[DBMaintenanceRecord]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(DBMaintenanceRecord).where(
                DBMaintenanceRecord.vehicle_id == vehicle_id
            )
        )
        return list(result.scalars())


async def _read_alerts(vehicle_id: str) -> list[Alert]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Alert).where(Alert.vehicle_id == vehicle_id)
        )
        return list(result.scalars())


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

async def _scenario() -> None:
    await init_db()

    svc = PersistenceService()

    suffix = uuid4().hex[:8]
    vehicle_id = f"v-{suffix}"
    driver_id = f"d-{suffix}"
    route_id = f"r-{suffix}"
    trip_id = f"t-{suffix}"

    await _cleanup(vehicle_id, driver_id, route_id, trip_id)

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
        await svc.create_trip(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            start_time=datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        )

        # --------------------------------------------------------------
        # Flow 1 — HealthSnapshot ──► vehicle_health
        # --------------------------------------------------------------
        snapshot_store = AnalyticsSnapshotStore()
        state = IntelligenceState()
        health_consumer = VehicleHealthConsumer(
            engine=VehicleHealthEngine(
                analyzers=(
                    EngineHealthAnalyzer(),
                    BrakeHealthAnalyzer(),
                    CoolingHealthAnalyzer(),
                    TransmissionHealthAnalyzer(),
                    FuelSystemHealthAnalyzer(),
                )
            ),
            snapshot_store=snapshot_store,
            state=state,
        )
        pipeline = TelemetryPipeline()
        pipeline.register(health_consumer)

        sample = _make_sample(vehicle_id, driver_id, trip_id)
        snapshot_store.update(
            _make_analytics_snapshot(vehicle_id, driver_id, trip_id, sample)
        )
        pipeline.publish(sample)

        health: HealthSnapshot | None = health_consumer.get_latest(vehicle_id)
        assert health is not None
        assert health.vehicle_id == vehicle_id

        await svc.persist_vehicle_health(health)

        health_row = await _read_vehicle_health(vehicle_id)
        assert health_row.vehicle_id == vehicle_id
        assert abs(health_row.overall_health_score - health.overall_health_score) < 0.01
        assert abs(health_row.engine_health - health.engine_health.score) < 0.01
        assert abs(health_row.cooling_health - health.cooling_health.score) < 0.01

        # --------------------------------------------------------------
        # Flow 2 — DriverStatistics ──► driver_statistics
        # --------------------------------------------------------------
        stats_state = IntelligenceState()
        stats_consumer = DriverStatisticsConsumer(
            engine=DriverStatisticsEngine(
                score_calculator=DriverScoreCalculator()
            ),
            state=stats_state,
        )

        trip = DomainTrip(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            distance_travelled_km=25.0,
        )
        events = [
            _make_event(vehicle_id, driver_id, trip_id, "harsh_braking"),
            _make_event(vehicle_id, driver_id, trip_id, "speeding"),
            _make_event(vehicle_id, driver_id, trip_id, "aggressive_throttle"),
            _make_event(vehicle_id, driver_id, trip_id, "high_rpm"),
        ]
        statistics = stats_consumer.record_trip(
            driver_id=driver_id,
            behaviour_events=events,
            trip=trip,
        )
        assert statistics.driver_id == driver_id

        await svc.persist_driver_statistics(statistics)

        stats_row = await _read_driver_statistics(driver_id)
        assert stats_row.driver_id == driver_id
        assert abs(stats_row.safety_score - statistics.safety_score) < 0.01
        assert abs(stats_row.aggression_score - statistics.aggression_score) < 0.01
        assert abs(stats_row.efficiency_score - statistics.efficiency_score) < 0.01
        assert stats_row.total_trips == statistics.total_trips == 1
        assert abs(stats_row.total_distance_km - statistics.total_distance) < 0.01
        assert stats_row.speeding_events == statistics.overspeed_count == 1
        assert stats_row.harsh_braking_events == statistics.harsh_braking_count == 1

        # --------------------------------------------------------------
        # Flow 3 — MaintenanceService ──► maintenance_records
        # --------------------------------------------------------------
        maintenance_service = MaintenanceService(
            estimators=(
                EngineEstimator(),
                BrakeEstimator(),
                CoolingEstimator(),
                TransmissionEstimator(),
                FuelSystemEstimator(),
            )
        )
        recommendations = maintenance_service.estimate_maintenance(
            health_snapshot=health,
            vehicle=vehicle,
            telemetry_sample=sample,
            odometer_km=vehicle.odometer_km,
        )
        records = maintenance_service.build_records(
            recommendations=recommendations,
            odometer_km=vehicle.odometer_km,
        )
        assert len(records) > 0

        await svc.persist_maintenance_records(records)

        record_rows = await _read_maintenance_records(vehicle_id)
        assert len(record_rows) == len(records)
        persisted_types = {row.maintenance_type for row in record_rows}
        expected_types = {
            record.maintenance_type.value for record in records
        }
        assert persisted_types == expected_types

        # --------------------------------------------------------------
        # Flow 4 — AlertEngine ──► alerts
        # --------------------------------------------------------------
        alert_engine = AlertEngine(
            generators=(
                HealthAlertsGenerator(),
                TelemetryAlertsGenerator(),
                MaintenanceAlertsGenerator(),
                TripAlertsGenerator(),
            )
        )
        alerts = alert_engine.generate_alerts(
            recommendations=recommendations,
            health_snapshot=health,
            telemetry=(sample,),
            trip=trip,
            behaviour_events=events,
        )
        assert len(alerts) > 0

        await svc.persist_alerts(alerts)

        alert_rows = await _read_alerts(vehicle_id)
        assert len(alert_rows) == len(alerts)
        persisted_signals = Counter(
            (row.alert_type, row.severity) for row in alert_rows
        )
        expected_signals = Counter(
            (alert.alert_type.value, alert.severity.value)
            for alert in alerts
        )
        assert persisted_signals == expected_signals
        for row in alert_rows:
            assert len(row.alert_id) <= 36
    finally:
        await _cleanup(vehicle_id, driver_id, route_id, trip_id)
        await close_db()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIntelligencePersistence:
    async def test_intelligence_outputs_are_persisted(self) -> None:
        await _scenario()
