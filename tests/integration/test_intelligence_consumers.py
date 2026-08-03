"""
Smoke tests for Fleet Intelligence Phase 1 wiring.

Proves the two intelligence flows end-to-end through the application
consumers:

    TelemetrySample ──► VehicleHealthEngine ──► HealthSnapshot
    BehaviourEvents + Trip ──► DriverStatisticsEngine ──► DriverStatistics

Also verifies DriveVitalsRuntime wires both consumers into the existing
telemetry pipeline and trip-completion flow.
"""

import sys
import os
from datetime import datetime, timezone

# Ensure backend/ is on sys.path so backend.* resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.driver_statistics import (
    DriverScoreCalculator,
    DriverStatistics,
    DriverStatisticsEngine,
)
from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)
from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)
from backend.analytics.vehicle_health import (
    HealthSnapshot,
    VehicleHealthEngine,
)
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
from backend.application.consumers.driver_statistics_consumer import (
    DriverStatisticsConsumer,
)
from backend.application.consumers.vehicle_health_consumer import (
    VehicleHealthConsumer,
)
from backend.application.intelligence_state import (
    IntelligenceState,
)
from backend.fleet.models.trip import (
    Trip,
)
from backend.pipeline.telemetry_pipeline import (
    TelemetryPipeline,
)
from backend.telemetry.models.telemetry_sample import (
    TelemetrySample,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample(
    vehicle_id: str = "vehicle-a",
    driver_id: str = "driver-1",
    trip_id: str = "trip-1",
    timestamp: datetime | None = None,
) -> TelemetrySample:
    return TelemetrySample(
        timestamp=timestamp or datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        speed_kmh=55.0,
        rpm=2200.0,
        throttle_position_percent=35.0,
        brake_pressure=0.0,
        coolant_temperature_c=90.0,
        engine_load_percent=45.0,
        fuel_rate_lph=8.0,
        fuel_level_percent=60.0,
        odometer_km=1000.0,
    )


def _make_snapshot(
    vehicle_id: str = "vehicle-a",
    driver_id: str = "driver-1",
    trip_id: str = "trip-1",
) -> AnalyticsSnapshot:
    sample = _make_sample(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
    )
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
            speeding=False,
            speed_excess_kmh=0.0,
            harsh_braking=False,
            aggressive_throttle=False,
            high_rpm=False,
            severity="normal",
            odometer_km=sample.odometer_km,
        ),
        completed_events=(),
        active_event_types=(),
    )


def _make_vehicle_health_engine() -> VehicleHealthEngine:
    return VehicleHealthEngine(
        analyzers=(
            EngineHealthAnalyzer(),
            BrakeHealthAnalyzer(),
            CoolingHealthAnalyzer(),
            TransmissionHealthAnalyzer(),
            FuelSystemHealthAnalyzer(),
        )
    )


def _make_event(
    event_type: str,
    driver_id: str = "driver-1",
    trip_id: str = "trip-1",
) -> BehaviourEvent:
    started = datetime(2026, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    return BehaviourEvent(
        vehicle_id="vehicle-a",
        driver_id=driver_id,
        trip_id=trip_id,
        event_type=event_type,
        started_at=started,
        ended_at=started,
        duration_seconds=5.0,
        distance_km=0.1,
        severity="moderate",
    )


# ---------------------------------------------------------------------------
# Flow 1 — TelemetrySample ──► VehicleHealthEngine ──► HealthSnapshot
# ---------------------------------------------------------------------------

class TestVehicleHealthFlow:
    """Proves the vehicle health chain through the application consumer."""

    def test_telemetry_sample_produces_health_snapshot(self):
        state = IntelligenceState()
        snapshot_store = AnalyticsSnapshotStore()
        consumer = VehicleHealthConsumer(
            engine=_make_vehicle_health_engine(),
            snapshot_store=snapshot_store,
            state=state,
        )

        pipeline = TelemetryPipeline()
        pipeline.register(consumer)
        snapshot_store.update(_make_snapshot())

        sample = _make_sample()
        pipeline.publish(sample)

        health = consumer.get_latest("vehicle-a")
        assert health is not None
        assert isinstance(health, HealthSnapshot)
        assert health.vehicle_id == "vehicle-a"
        assert health.trip_id == "trip-1"
        assert 0.0 <= health.overall_health_score <= 100.0
        assert health.engine_health is not None
        assert health.cooling_health is not None
        assert health.transmission_health is not None
        assert health.brake_health is not None
        assert health.fuel_system_health is not None

    def test_consumer_skips_until_analytics_snapshot_exists(self):
        state = IntelligenceState()
        consumer = VehicleHealthConsumer(
            engine=_make_vehicle_health_engine(),
            snapshot_store=AnalyticsSnapshotStore(),
            state=state,
        )

        pipeline = TelemetryPipeline()
        pipeline.register(consumer)

        pipeline.publish(_make_sample())

        assert consumer.get_latest("vehicle-a") is None


# ---------------------------------------------------------------------------
# Flow 2 — BehaviourEvents + Trip ──► DriverStatisticsEngine ──► DriverStatistics
# ---------------------------------------------------------------------------

class TestDriverStatisticsFlow:
    """Proves the driver statistics chain through the application consumer."""

    def test_events_and_trip_produce_driver_statistics(self):
        state = IntelligenceState()
        consumer = DriverStatisticsConsumer(
            engine=DriverStatisticsEngine(
                score_calculator=DriverScoreCalculator()
            ),
            state=state,
        )

        trip = Trip(
            trip_id="trip-1",
            vehicle_id="vehicle-a",
            driver_id="driver-1",
            route_id="route-1",
            distance_travelled_km=12.0,
        )

        consumer.record_trip(
            driver_id="driver-1",
            behaviour_events=[
                _make_event(event_type="harsh_braking"),
                _make_event(event_type="speeding"),
            ],
            trip=trip,
        )

        stats = consumer.get_latest("driver-1")
        assert stats is not None
        assert isinstance(stats, DriverStatistics)
        assert stats.driver_id == "driver-1"
        assert stats.total_trips == 1
        assert stats.total_events == 2
        assert stats.harsh_braking_count == 1
        assert stats.overspeed_count == 1
        assert stats.harsh_acceleration_count == 0
        assert stats.total_distance == 12.0
        assert 0.0 <= stats.safety_score <= 100.0
        assert 0.0 <= stats.aggression_score <= 100.0
        assert 0.0 <= stats.efficiency_score <= 100.0

    def test_statistics_accumulate_across_trips(self):
        state = IntelligenceState()
        consumer = DriverStatisticsConsumer(
            engine=DriverStatisticsEngine(
                score_calculator=DriverScoreCalculator()
            ),
            state=state,
        )

        consumer.record_trip(
            driver_id="driver-1",
            behaviour_events=[
                _make_event(event_type="harsh_braking"),
            ],
            trip=Trip(
                trip_id="trip-1",
                vehicle_id="vehicle-a",
                driver_id="driver-1",
                route_id="route-1",
                distance_travelled_km=5.0,
            ),
        )
        consumer.record_trip(
            driver_id="driver-1",
            behaviour_events=[
                _make_event(event_type="high_rpm"),
            ],
            trip=Trip(
                trip_id="trip-2",
                vehicle_id="vehicle-a",
                driver_id="driver-1",
                route_id="route-1",
                distance_travelled_km=7.0,
            ),
        )

        stats = consumer.get_latest("driver-1")
        assert stats is not None
        assert stats.total_trips == 2
        assert stats.total_events == 2
        assert stats.total_distance == 12.0


# ---------------------------------------------------------------------------
# Flow 3 — DriveVitalsRuntime wiring
# ---------------------------------------------------------------------------

class TestRuntimeWiring:
    """Proves the runtime wires intelligence into the existing flows."""

    def test_runtime_registers_consumers(self):
        from backend.application.runtime import DriveVitalsRuntime

        runtime = DriveVitalsRuntime()

        # AnalyticsEngine + VehicleHealthConsumer in the telemetry pipeline.
        assert runtime.telemetry_pipeline.consumer_count == 2

        assert isinstance(runtime.intelligence_state, IntelligenceState)
        assert isinstance(runtime.vehicle_health_engine, VehicleHealthEngine)
        assert isinstance(runtime.vehicle_health_consumer, VehicleHealthConsumer)
        assert isinstance(runtime.driver_statistics_engine, DriverStatisticsEngine)
        assert isinstance(runtime.driver_statistics_consumer, DriverStatisticsConsumer)

    def test_runtime_produces_health_snapshot_via_pipeline(self):
        from backend.application.runtime import DriveVitalsRuntime

        runtime = DriveVitalsRuntime()

        runner = runtime.fleet._runners[0]
        sample = _make_sample(
            vehicle_id=runner.vehicle.vehicle_id,
            driver_id=runner.driver.driver_id,
            trip_id=runner.trip.trip_id,
        )

        runtime.telemetry_pipeline.publish(sample)

        health = runtime.intelligence_state.get_health_snapshot(
            runner.vehicle.vehicle_id
        )
        assert health is not None
        assert health.vehicle_id == runner.vehicle.vehicle_id
        assert health.trip_id == runner.trip.trip_id
