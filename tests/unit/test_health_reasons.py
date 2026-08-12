"""Unit tests for the canonical vehicle health reasons pipeline."""

import json
from dataclasses import asdict
from datetime import datetime, timezone

from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    health_config_to_dict,
)
from backend.analytics.vehicle_health.health_reasons import (
    flatten_health_reasons,
)
from backend.analytics.vehicle_health.models.health_reason import (
    HealthReason,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
    Subsystem,
    SubsystemHealth,
)


def _subsystem(subsystem, reasons=()):
    return SubsystemHealth(
        subsystem=subsystem,
        score=80.0,
        status=HealthStatus.WARNING,
        reasons=reasons,
    )


def _snapshot(engine=(), cooling=(), brake=(), transmission=(), fuel=()):
    return HealthSnapshot(
        vehicle_id="v-1",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        overall_health_score=80.0,
        overall_status=HealthStatus.WARNING,
        engine_health=_subsystem(Subsystem.ENGINE, engine),
        cooling_health=_subsystem(Subsystem.COOLING, cooling),
        transmission_health=_subsystem(Subsystem.TRANSMISSION, transmission),
        brake_health=_subsystem(Subsystem.BRAKES, brake),
        fuel_system_health=_subsystem(Subsystem.FUEL_SYSTEM, fuel),
    )


def test_flatten_none_snapshot_is_empty():
    assert flatten_health_reasons(None) == ()


def test_flatten_snapshot_without_reasons_is_empty():
    assert flatten_health_reasons(_snapshot()) == ()


def test_flatten_orders_subsystems_canonically():
    health = _snapshot(
        transmission=("repeated drivetrain stress (40% of window)",),
        cooling=("elevated coolant temperature (95 C)",),
        engine=("engine overheating (107 C)",),
    )
    reasons = flatten_health_reasons(health)

    assert [r.subsystem for r in reasons] == [
        "engine",
        "cooling",
        "transmission",
    ]


def test_flatten_preserves_subsystem_reason_order():
    health = _snapshot(
        engine=(
            "engine overheating (107 C)",
            "rpm above redline (6600 rpm)",
            "sustained high engine load (55% of window)",
        ),
    )
    reasons = flatten_health_reasons(health)

    assert [r.reason for r in reasons] == [
        "engine overheating (107 C)",
        "rpm above redline (6600 rpm)",
        "sustained high engine load (55% of window)",
    ]


def test_flatten_deduplicates_exact_repeat_reasons():
    health = _snapshot(
        engine=("rpm above redline (6600 rpm)", "rpm above redline (6600 rpm)"),
    )
    reasons = flatten_health_reasons(health)

    assert len(reasons) == 1


def test_flatten_skips_empty_reason_strings():
    health = _snapshot(
        engine=("", "engine overheating (107 C)", ""),
    )
    reasons = flatten_health_reasons(health)

    assert [r.reason for r in reasons] == ["engine overheating (107 C)"]


def test_reason_to_dict_matches_websocket_asdict_shape():
    reason = HealthReason(
        subsystem="engine",
        reason="engine overheating (107 C)",
        code="ENGINE_OVERHEATING",
        title="Engine overheating",
        severity="critical",
        summary="engine overheating (107 C)",
        evidence={"temperature_c": 107.0},
        impact="Overheating can warp cylinder heads, damage gaskets, and cause total engine failure.",
        recommendation="Stop the vehicle safely, allow the engine to cool, and inspect the cooling system immediately.",
    )

    expected = {
        "subsystem": "engine",
        "reason": "engine overheating (107 C)",
        "code": "ENGINE_OVERHEATING",
        "title": "Engine overheating",
        "severity": "critical",
        "summary": "engine overheating (107 C)",
        "evidence": {"temperature_c": 107.0},
        "impact": "Overheating can warp cylinder heads, damage gaskets, and cause total engine failure.",
        "recommendation": "Stop the vehicle safely, allow the engine to cool, and inspect the cooling system immediately.",
    }
    assert reason.to_dict() == asdict(reason) == expected


def test_health_config_to_dict_is_json_friendly():
    data = health_config_to_dict(DEFAULT_HEALTH_CONFIG)

    assert data["weights"]["engine"] == 0.30
    assert data["status"]["healthy_min"] == 90.0
    assert data["engine"]["redline_rpm"] == 6200.0
    assert data["cooling"]["overheat_temp_c"] == 100.0
    assert data["brake"]["harsh_brake_pressure"] == 0.80
    assert data["transmission"]["stress_rpm"] == 4500.0
    assert data["fuel_system"]["min_efficiency_km_per_l"] == 6.0

    # Everything the config endpoint returns must be JSON-serializable.
    json.dumps(data)
