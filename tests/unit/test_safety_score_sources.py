"""M5.2 regression tests for safety-score truthfulness.

The forensic audit found two competing scores exposed to the UI:

* the canonical driver safety score
  (``driver_statistics.safety_score``, computed by
  ``analytics.driver_statistics.safety`` from completed-trip behaviour
  density), and
* a fabricated live score produced by
  ``DashboardBuilder._compute_driver_safety`` — a moment-to-moment
  deduction from *currently active* events that read 100.0 whenever no
  event happened to be active, plus a second ``_compute_risk_level``
  banding that disagreed with the canonical mapping.

``docs/driver_page_data_contract.md`` §2 states the required model: live
event state, driver safety score, trip safety score and current risk
state are four distinct things, and there is exactly one driver safety
score. These tests prove the API exposes only that one score and that no
contradictory pair can reappear.
"""

import dataclasses
from datetime import datetime

from backend.analytics.behaviour.aggregation.summarizer import (
    DriverBehaviourSummarizer,
)
from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)
from backend.analytics.behaviour.events.tracker import BehaviourEventTracker
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.context.context_store import AnalyticsContextStore
from backend.analytics.engine.analytics_engine import AnalyticsEngine
from backend.analytics.snapshot.snapshot_store import AnalyticsSnapshotStore
from backend.analytics.state.runtime_state_store import RuntimeStateStore
from backend.api.websocket.dashboard import _serialize
from backend.dashboard.schemas.dashboard_payload import (
    VehicleDashboardSummary,
)
from backend.dashboard.services.dashboard_builder import DashboardBuilder
from backend.streaming.snapshot_stream import AnalyticsSnapshotStream
from backend.telemetry.models.telemetry_sample import TelemetrySample

RETIRED_FIELDS = ("driver_safety_score", "driver_risk_level")


def _sample(speed_kmh: float = 80.0) -> TelemetrySample:
    return TelemetrySample(
        timestamp=datetime(2026, 9, 26, 12, 0, 0),
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        speed_kmh=speed_kmh,
        rpm=2500.0,
        throttle_position_percent=40.0,
        brake_pressure=0.1,
        coolant_temperature_c=90.0,
        engine_load_percent=45.0,
        fuel_rate_lph=6.5,
        fuel_level_percent=75.0,
        odometer_km=12000.0,
    )


def _snapshot():
    context_store = AnalyticsContextStore()
    engine = AnalyticsEngine(
        runtime_store=RuntimeStateStore(),
        context_store=context_store,
        driver_behaviour_analyzer=DriverBehaviourAnalyzer(),
        event_tracker=BehaviourEventTracker(),
        behaviour_summarizer=DriverBehaviourSummarizer(),
        snapshot_store=AnalyticsSnapshotStore(),
        snapshot_stream=AnalyticsSnapshotStream(),
    )
    context_store.register(
        AnalyticsContext(
            vehicle_id="V-1",
            driver_id="D-1",
            trip_id="T-1",
            route_id="R-1",
            route_type="urban",
            speed_limit_kmh=50.0,
            vehicle_make="Toyota",
            vehicle_model="Camry",
            vehicle_year=2024,
        )
    )
    return engine.consume(_sample())


class TestDashboardPayloadHasNoFabricatedScore:
    def test_summary_dataclass_drops_the_fabricated_fields(self) -> None:
        field_names = {
            f.name for f in dataclasses.fields(VehicleDashboardSummary)
        }
        for retired in RETIRED_FIELDS:
            assert retired not in field_names, (
                f"{retired} is a fabricated live score; it must not be part "
                "of the dashboard contract"
            )

    def test_live_event_state_is_still_exposed(self) -> None:
        """Live state remains available — it is simply not a score."""
        field_names = {
            f.name for f in dataclasses.fields(VehicleDashboardSummary)
        }
        assert {
            "active_event_types",
            "speeding",
            "harsh_braking",
            "aggressive_throttle",
            "high_rpm",
        } <= field_names

    def test_built_snapshot_carries_no_safety_score(self) -> None:
        builder = DashboardBuilder(AnalyticsContextStore())
        payload = builder.update(_snapshot())

        assert payload.vehicles, "expected one vehicle summary"
        vehicle = payload.vehicles[0]
        for retired in RETIRED_FIELDS:
            assert not hasattr(vehicle, retired)

    def test_websocket_payload_carries_no_safety_score(self) -> None:
        """The exact dict the browser receives must not contain them."""
        builder = DashboardBuilder(AnalyticsContextStore())
        serialized = _serialize(builder.update(_snapshot()))

        vehicle = serialized["vehicles"][0]
        for retired in RETIRED_FIELDS:
            assert retired not in vehicle, (
                f"{retired} still reaches the frontend dashboard payload"
            )
        # The canonical vehicle health score is unaffected.
        assert "overall_health_score" in vehicle


class TestApiExposesExactlyOneSafetyScore:
    """API-level proof: one authoritative driver safety score."""

    def test_openapi_schema_has_no_second_safety_score(self) -> None:
        from backend.api.main import app

        schema = app.openapi()
        offenders: list[tuple[str, str]] = []
        for model_name, model in schema.get("components", {}).get(
            "schemas", {}
        ).items():
            for property_name in (model.get("properties") or {}):
                if property_name in RETIRED_FIELDS:
                    offenders.append((model_name, property_name))

        assert not offenders, (
            f"API schema exposes retired safety fields: {offenders}. The only "
            "driver safety score is DriverStatisticsRead.safety_score."
        )

    def test_canonical_score_is_still_exposed(self) -> None:
        from backend.api.main import app

        schema = app.openapi()
        properties = schema["components"]["schemas"][
            "DriverStatisticsRead"
        ]["properties"]
        assert "safety_score" in properties, (
            "the canonical driver safety score must remain available to the UI"
        )

    def test_trip_score_is_a_distinct_metric(self) -> None:
        """Trip-level scoring is legitimate and separate from driver score."""
        from backend.api.main import app

        schema = app.openapi()
        trip_properties = schema["components"]["schemas"]["TripRead"][
            "properties"
        ]
        assert "safety_score" in trip_properties, (
            "the per-trip safety score is a distinct canonical metric"
        )
        assert "grade" in trip_properties
        assert "driver_safety_score" not in trip_properties
