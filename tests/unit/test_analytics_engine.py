"""Unit tests for AnalyticsEngine integration with its analytics dependencies."""

from datetime import datetime

from backend.analytics.behaviour.aggregation.summarizer import (
    DriverBehaviourSummarizer,
)
from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)
from backend.analytics.behaviour.events.tracker import (
    BehaviourEventTracker,
)
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.context.context_store import AnalyticsContextStore
from backend.analytics.engine.analytics_engine import AnalyticsEngine
from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.snapshot.snapshot_store import AnalyticsSnapshotStore
from backend.analytics.state.runtime_state_store import RuntimeStateStore
from backend.streaming.snapshot_stream import AnalyticsSnapshotStream
from backend.telemetry.models.telemetry_sample import TelemetrySample


def _make_sample(
    vehicle_id: str = "V-1",
    driver_id: str = "D-1",
    trip_id: str = "T-1",
    speed_kmh: float = 80.0,
    fuel_level_percent: float = 75.0,
    timestamp: datetime | None = None,
) -> TelemetrySample:
    return TelemetrySample(
        timestamp=timestamp or datetime(2025, 1, 1, 12, 0, 0),
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        speed_kmh=speed_kmh,
        rpm=2500.0,
        throttle_position_percent=0.4,
        brake_pressure=0.1,
        coolant_temperature_c=90.0,
        engine_load_percent=45.0,
        fuel_rate_lph=6.5,
        fuel_level_percent=fuel_level_percent,
        odometer_km=12000.0,
    )


def _make_context(
    vehicle_id: str = "V-1",
    driver_id: str = "D-1",
    trip_id: str = "T-1",
    speed_limit_kmh: float = 60.0,
) -> AnalyticsContext:
    return AnalyticsContext(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        route_id="R-1",
        route_type="urban",
        speed_limit_kmh=speed_limit_kmh,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        vehicle_year=2024,
    )


def _make_engine(
    runtime_store: RuntimeStateStore | None = None,
) -> tuple[
    AnalyticsEngine,
    RuntimeStateStore,
    AnalyticsContextStore,
    AnalyticsSnapshotStore,
    AnalyticsSnapshotStream,
]:
    if runtime_store is None:
        runtime_store = RuntimeStateStore()
    context_store = AnalyticsContextStore()
    snapshot_store = AnalyticsSnapshotStore()
    snapshot_stream = AnalyticsSnapshotStream()

    engine = AnalyticsEngine(
        runtime_store=runtime_store,
        context_store=context_store,
        driver_behaviour_analyzer=DriverBehaviourAnalyzer(),
        event_tracker=BehaviourEventTracker(),
        behaviour_summarizer=DriverBehaviourSummarizer(),
        snapshot_store=snapshot_store,
        snapshot_stream=snapshot_stream,
    )
    return engine, runtime_store, context_store, snapshot_store, snapshot_stream


class TestEngineConstruction:
    def test_accepts_runtime_store(self):
        store = RuntimeStateStore()
        engine, _, _, _, _ = _make_engine(runtime_store=store)
        assert engine.runtime_store is store

    def test_runtime_store_is_accessible(self):
        engine, _, _, _, _ = _make_engine()
        assert isinstance(engine.runtime_store, RuntimeStateStore)


class TestConsumeCreatesState:
    def test_first_sample_creates_state(self):
        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context())

        engine.consume(_make_sample())

        assert len(store) == 1
        state = store.get("V-1")
        assert state is not None
        assert state.vehicle_id == "V-1"

    def test_returns_snapshot(self):
        engine, _, context_store, snapshot_store, _ = _make_engine()
        context_store.register(_make_context())

        result = engine.consume(_make_sample())

        assert isinstance(result, AnalyticsSnapshot)
        assert result.vehicle_id == "V-1"
        assert result.driver_id == "D-1"
        assert result.trip_id == "T-1"
        assert snapshot_store.get("V-1") is result

    def test_requires_registered_context(self):
        from pytest import raises

        engine, _, _, _, _ = _make_engine()

        with raises(ValueError, match="No analytics context"):
            engine.consume(_make_sample())


class TestConsumeUpdatesState:
    def test_second_sample_updates_state(self):
        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context())

        engine.consume(_make_sample(speed_kmh=80.0))
        engine.consume(_make_sample(speed_kmh=95.0))

        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 95.0
        assert len(store) == 1

    def test_latest_values_wins(self):
        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context())

        engine.consume(_make_sample(speed_kmh=60.0, fuel_level_percent=80.0))
        engine.consume(_make_sample(speed_kmh=100.0, fuel_level_percent=70.0))

        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 100.0
        assert state.fuel_level_percent == 70.0


class TestConsumeMultipleVehicles:
    def test_vehicles_remain_independent(self):
        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context(vehicle_id="V-1"))
        context_store.register(_make_context(vehicle_id="V-2"))

        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        engine.consume(_make_sample(vehicle_id="V-2", speed_kmh=110.0))

        s1 = store.get("V-1")
        s2 = store.get("V-2")
        assert s1 is not None and s1.speed_kmh == 60.0
        assert s2 is not None and s2.speed_kmh == 110.0
        assert len(store) == 2

    def test_updating_one_does_not_affect_another(self):
        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context(vehicle_id="V-1"))
        context_store.register(_make_context(vehicle_id="V-2"))

        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        engine.consume(_make_sample(vehicle_id="V-2", speed_kmh=110.0))
        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=70.0))

        s2 = store.get("V-2")
        assert s2 is not None
        assert s2.speed_kmh == 110.0


class TestPipelineIntegration:
    def test_engine_works_as_consumer(self):
        from backend.pipeline.telemetry_pipeline import TelemetryPipeline

        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context())
        pipeline = TelemetryPipeline()

        pipeline.register(engine)
        pipeline.publish(_make_sample())

        assert len(store) == 1
        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 80.0

    def test_pipeline_multiple_samples(self):
        from backend.pipeline.telemetry_pipeline import TelemetryPipeline

        engine, store, context_store, _, _ = _make_engine()
        context_store.register(_make_context(vehicle_id="V-1"))
        context_store.register(_make_context(vehicle_id="V-2"))
        pipeline = TelemetryPipeline()
        pipeline.register(engine)

        pipeline.publish(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        pipeline.publish(_make_sample(vehicle_id="V-2", speed_kmh=110.0))
        pipeline.publish(_make_sample(vehicle_id="V-1", speed_kmh=70.0))

        assert len(store) == 2
        assert store.get("V-1").speed_kmh == 70.0
        assert store.get("V-2").speed_kmh == 110.0
