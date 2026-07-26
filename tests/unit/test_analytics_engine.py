"""Unit tests for AnalyticsEngine integration with RuntimeStateStore."""

from datetime import datetime

from backend.analytics.engine.analytics_engine import AnalyticsEngine
from backend.analytics.state.runtime_state_store import RuntimeStateStore
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


class TestEngineConstruction:
    def test_accepts_store(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)
        assert engine.store is store

    def test_store_is_accessible(self):
        engine = AnalyticsEngine(RuntimeStateStore())
        assert isinstance(engine.store, RuntimeStateStore)


class TestConsumeCreatesState:
    def test_first_sample_creates_state(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)

        engine.consume(_make_sample())

        assert len(store) == 1
        state = store.get("V-1")
        assert state is not None
        assert state.vehicle_id == "V-1"

    def test_returns_nothing(self):
        engine = AnalyticsEngine(RuntimeStateStore())
        result = engine.consume(_make_sample())
        assert result is None


class TestConsumeUpdatesState:
    def test_second_sample_updates_state(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)

        engine.consume(_make_sample(speed_kmh=80.0))
        engine.consume(_make_sample(speed_kmh=95.0))

        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 95.0
        assert len(store) == 1

    def test_latest_values_wins(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)

        engine.consume(_make_sample(speed_kmh=60.0, fuel_level_percent=80.0))
        engine.consume(_make_sample(speed_kmh=100.0, fuel_level_percent=70.0))

        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 100.0
        assert state.fuel_level_percent == 70.0


class TestConsumeMultipleVehicles:
    def test_vehicles_remain_independent(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)

        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        engine.consume(_make_sample(vehicle_id="V-2", speed_kmh=110.0))

        s1 = store.get("V-1")
        s2 = store.get("V-2")
        assert s1 is not None and s1.speed_kmh == 60.0
        assert s2 is not None and s2.speed_kmh == 110.0
        assert len(store) == 2

    def test_updating_one_does_not_affect_another(self):
        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)

        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        engine.consume(_make_sample(vehicle_id="V-2", speed_kmh=110.0))
        engine.consume(_make_sample(vehicle_id="V-1", speed_kmh=70.0))

        s2 = store.get("V-2")
        assert s2 is not None
        assert s2.speed_kmh == 110.0


class TestPipelineIntegration:
    def test_engine_works_as_consumer(self):
        from backend.pipeline.telemetry_pipeline import TelemetryPipeline

        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)
        pipeline = TelemetryPipeline()

        pipeline.register(engine)
        pipeline.publish(_make_sample())

        assert len(store) == 1
        state = store.get("V-1")
        assert state is not None
        assert state.speed_kmh == 80.0

    def test_pipeline_multiple_samples(self):
        from backend.pipeline.telemetry_pipeline import TelemetryPipeline

        store = RuntimeStateStore()
        engine = AnalyticsEngine(store)
        pipeline = TelemetryPipeline()
        pipeline.register(engine)

        pipeline.publish(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        pipeline.publish(_make_sample(vehicle_id="V-2", speed_kmh=110.0))
        pipeline.publish(_make_sample(vehicle_id="V-1", speed_kmh=70.0))

        assert len(store) == 2
        assert store.get("V-1").speed_kmh == 70.0
        assert store.get("V-2").speed_kmh == 110.0
