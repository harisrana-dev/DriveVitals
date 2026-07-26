"""Unit tests for AnalyticsContext and AnalyticsContextStore."""

import pytest

from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.context.context_store import AnalyticsContextStore


def _make_context(
    vehicle_id: str = "V-1",
    driver_id: str = "D-1",
    trip_id: str = "T-1",
    route_id: str = "R-1",
    route_type: str = "urban",
    speed_limit_kmh: float = 60.0,
    vehicle_make: str = "Toyota",
    vehicle_model: str = "Camry",
    vehicle_year: int = 2024,
) -> AnalyticsContext:
    return AnalyticsContext(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        route_id=route_id,
        route_type=route_type,
        speed_limit_kmh=speed_limit_kmh,
        vehicle_make=vehicle_make,
        vehicle_model=vehicle_model,
        vehicle_year=vehicle_year,
    )


class TestContextConstruction:
    def test_valid_context_can_be_created(self):
        ctx = _make_context()

        assert ctx.vehicle_id == "V-1"
        assert ctx.driver_id == "D-1"
        assert ctx.trip_id == "T-1"
        assert ctx.route_id == "R-1"
        assert ctx.route_type == "urban"
        assert ctx.speed_limit_kmh == 60.0
        assert ctx.vehicle_make == "Toyota"
        assert ctx.vehicle_model == "Camry"
        assert ctx.vehicle_year == 2024

    def test_context_is_immutable(self):
        ctx = _make_context()

        with pytest.raises(AttributeError):
            ctx.speed_limit_kmh = 120.0  # type: ignore[misc]

    def test_context_with_different_values(self):
        ctx = _make_context(
            vehicle_id="V-99",
            driver_id="D-42",
            trip_id="T-7",
            route_type="highway",
            speed_limit_kmh=130.0,
            vehicle_make="Honda",
            vehicle_model="Civic",
            vehicle_year=2023,
        )

        assert ctx.vehicle_id == "V-99"
        assert ctx.route_type == "highway"
        assert ctx.speed_limit_kmh == 130.0
        assert ctx.vehicle_year == 2023


class TestStoreRegistration:
    def test_first_context_can_be_registered(self):
        store = AnalyticsContextStore()
        ctx = _make_context()

        store.register(ctx)

        assert len(store) == 1

    def test_get_returns_same_context(self):
        store = AnalyticsContextStore()
        ctx = _make_context()
        store.register(ctx)

        retrieved = store.get("V-1")

        assert retrieved is ctx


class TestContextReplacement:
    def test_registering_same_vehicle_replaces_context(self):
        store = AnalyticsContextStore()
        ctx1 = _make_context(speed_limit_kmh=60.0)
        ctx2 = _make_context(speed_limit_kmh=130.0)

        store.register(ctx1)
        store.register(ctx2)

        retrieved = store.get("V-1")
        assert retrieved is ctx2
        assert retrieved is not ctx1
        assert len(store) == 1


class TestMultipleVehicles:
    def test_contexts_remain_independent(self):
        store = AnalyticsContextStore()
        ctx1 = _make_context(vehicle_id="V-1", speed_limit_kmh=60.0)
        ctx2 = _make_context(vehicle_id="V-2", speed_limit_kmh=130.0)

        store.register(ctx1)
        store.register(ctx2)

        r1 = store.get("V-1")
        r2 = store.get("V-2")

        assert r1 is not None
        assert r2 is not None
        assert r1.speed_limit_kmh == 60.0
        assert r2.speed_limit_kmh == 130.0
        assert len(store) == 2

    def test_updating_one_does_not_affect_another(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1", route_type="urban"))
        store.register(_make_context(vehicle_id="V-2", route_type="highway"))

        store.register(_make_context(vehicle_id="V-1", route_type="rural"))

        r2 = store.get("V-2")
        assert r2 is not None
        assert r2.route_type == "highway"
        assert len(store) == 2


class TestGet:
    def test_returns_none_for_unknown_vehicle(self):
        store = AnalyticsContextStore()
        assert store.get("UNKNOWN") is None

    def test_returns_context_for_known_vehicle(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        assert store.get("V-1") is not None


class TestRemove:
    def test_removes_one_vehicle(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))

        store.remove("V-1")

        assert store.get("V-1") is None
        assert store.get("V-2") is not None
        assert len(store) == 1

    def test_remove_unknown_is_noop(self):
        store = AnalyticsContextStore()
        store.remove("UNKNOWN")
        assert len(store) == 0


class TestClear:
    def test_removes_all_contexts(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))
        store.register(_make_context(vehicle_id="V-3"))

        store.clear()

        assert len(store) == 0
        assert store.all_contexts() == []


class TestAllContexts:
    def test_returns_current_contexts(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))

        contexts = store.all_contexts()

        assert len(contexts) == 2
        ids = {c.vehicle_id for c in contexts}
        assert ids == {"V-1", "V-2"}

    def test_returns_empty_list_when_empty(self):
        store = AnalyticsContextStore()
        assert store.all_contexts() == []

    def test_does_not_expose_internal_dictionary(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))

        contexts = store.all_contexts()
        contexts.clear()

        assert len(store) == 1


class TestLen:
    def test_returns_zero_for_empty_store(self):
        assert len(AnalyticsContextStore()) == 0

    def test_returns_count_of_tracked_vehicles(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))
        store.register(_make_context(vehicle_id="V-3"))
        assert len(store) == 3

    def test_len_after_remove(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))

        store.remove("V-1")

        assert len(store) == 1

    def test_len_after_clear(self):
        store = AnalyticsContextStore()
        store.register(_make_context(vehicle_id="V-1"))
        store.register(_make_context(vehicle_id="V-2"))

        store.clear()

        assert len(store) == 0
