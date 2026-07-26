"""Unit tests for RuntimeStateStore."""

from datetime import datetime

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


class TestFirstSample:
    def test_creates_state(self):
        store = RuntimeStateStore()
        sample = _make_sample()

        state = store.update(sample)

        assert state.vehicle_id == "V-1"
        assert state.driver_id == "D-1"
        assert state.trip_id == "T-1"
        assert state.speed_kmh == 80.0
        assert len(store) == 1

    def test_returns_runtime_analytics_state(self):
        from backend.analytics.state.runtime_state import RuntimeAnalyticsState

        store = RuntimeStateStore()
        state = store.update(_make_sample())
        assert isinstance(state, RuntimeAnalyticsState)


class TestSubsequentSamples:
    def test_second_sample_updates_state(self):
        store = RuntimeStateStore()
        store.update(_make_sample(speed_kmh=80.0))

        updated = store.update(_make_sample(speed_kmh=95.0))

        assert updated.speed_kmh == 95.0
        assert len(store) == 1

    def test_preserves_latest_values(self):
        store = RuntimeStateStore()
        store.update(_make_sample(speed_kmh=80.0, fuel_level_percent=75.0))

        updated = store.update(_make_sample(speed_kmh=100.0, fuel_level_percent=70.0))

        assert updated.speed_kmh == 100.0
        assert updated.fuel_level_percent == 70.0


class TestMultipleVehicles:
    def test_vehicles_remain_independent(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        store.update(_make_sample(vehicle_id="V-2", speed_kmh=110.0))

        state1 = store.get("V-1")
        state2 = store.get("V-2")

        assert state1 is not None
        assert state2 is not None
        assert state1.speed_kmh == 60.0
        assert state2.speed_kmh == 110.0
        assert len(store) == 2

    def test_updating_one_does_not_affect_another(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1", speed_kmh=60.0))
        store.update(_make_sample(vehicle_id="V-2", speed_kmh=110.0))

        store.update(_make_sample(vehicle_id="V-1", speed_kmh=70.0))

        state2 = store.get("V-2")
        assert state2 is not None
        assert state2.speed_kmh == 110.0
        assert len(store) == 2


class TestGet:
    def test_returns_none_for_unknown_vehicle(self):
        store = RuntimeStateStore()
        assert store.get("UNKNOWN") is None

    def test_returns_state_for_known_vehicle(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1"))
        assert store.get("V-1") is not None


class TestRemove:
    def test_removes_one_vehicle(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1"))
        store.update(_make_sample(vehicle_id="V-2"))

        store.remove("V-1")

        assert store.get("V-1") is None
        assert store.get("V-2") is not None
        assert len(store) == 1

    def test_remove_unknown_is_noop(self):
        store = RuntimeStateStore()
        store.remove("UNKNOWN")
        assert len(store) == 0


class TestClear:
    def test_removes_all_states(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1"))
        store.update(_make_sample(vehicle_id="V-2"))
        store.update(_make_sample(vehicle_id="V-3"))

        store.clear()

        assert len(store) == 0
        assert store.all_states() == []


class TestAllStates:
    def test_returns_current_states(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1"))
        store.update(_make_sample(vehicle_id="V-2"))

        states = store.all_states()

        assert len(states) == 2
        ids = {s.vehicle_id for s in states}
        assert ids == {"V-1", "V-2"}

    def test_returns_empty_list_when_empty(self):
        store = RuntimeStateStore()
        assert store.all_states() == []


class TestLen:
    def test_returns_zero_for_empty_store(self):
        assert len(RuntimeStateStore()) == 0

    def test_returns_count_of_tracked_vehicles(self):
        store = RuntimeStateStore()
        store.update(_make_sample(vehicle_id="V-1"))
        store.update(_make_sample(vehicle_id="V-2"))
        store.update(_make_sample(vehicle_id="V-3"))
        assert len(store) == 3
