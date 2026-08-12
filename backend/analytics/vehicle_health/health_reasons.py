"""
Health reason flattening.

Turns the per-subsystem reasons held by a HealthSnapshot into a single,
ordered, de-duplicated stream of HealthReason items for the dashboard
and REST layers. Each reason is enriched with structured metadata
(code, title, severity, evidence, impact, recommendation) so the
frontend can render explainable operational intelligence.

The subsystem order below is the canonical presentation order
(critical-path subsystems first). Within a subsystem, the analyzer's own
contribution order is preserved because analyzers emit their highest
priority deduction first.
"""

import re
from collections.abc import Mapping, Sequence

from backend.analytics.vehicle_health.models.health_reason import (
    HealthReason,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    SubsystemHealth,
)


_SUBSYSTEM_ORDER = (
    "engine",
    "cooling",
    "brakes",
    "transmission",
    "fuel_system",
)

_SUBSYSTEM_ATTRIBUTES = {
    "engine": "engine_health",
    "cooling": "cooling_health",
    "brakes": "brake_health",
    "transmission": "transmission_health",
    "fuel_system": "fuel_system_health",
}

# Mapping from reason string prefix to structured metadata.
# The first matching pattern wins.
_REASON_METADATA: tuple[tuple[str, dict[str, object]], ...] = (
    # Engine
    (
        "rpm above redline",
        {
            "code": "RPM_ABOVE_REDLINE",
            "title": "RPM above redline",
            "severity": "critical",
            "impact": "Extended redline operation increases engine wear and risks catastrophic failure.",
            "recommendation": "Monitor RPM during the next trip and avoid sustained redline operation.",
        },
    ),
    (
        "sustained high rpm",
        {
            "code": "SUSTAINED_HIGH_RPM",
            "title": "Sustained high RPM",
            "severity": "warning",
            "impact": "Prolonged high-RPM operation accelerates engine wear and fuel consumption.",
            "recommendation": "Review driving patterns to reduce time spent at high engine speeds.",
        },
    ),
    (
        "engine overheating",
        {
            "code": "ENGINE_OVERHEATING",
            "title": "Engine overheating",
            "severity": "critical",
            "impact": "Overheating can warp cylinder heads, damage gaskets, and cause total engine failure.",
            "recommendation": "Stop the vehicle safely, allow the engine to cool, and inspect the cooling system immediately.",
        },
    ),
    (
        "sustained high engine load",
        {
            "code": "SUSTAINED_HIGH_ENGINE_LOAD",
            "title": "Sustained high engine load",
            "severity": "warning",
            "impact": "Continuous high load strains bearings, pistons, and lubrication.",
            "recommendation": "Reduce load where possible and schedule an engine inspection at the next service interval.",
        },
    ),
    (
        "excessive throttle abuse",
        {
            "code": "EXCESSIVE_THROTTLE_ABUSE",
            "title": "Excessive throttle abuse",
            "severity": "warning",
            "impact": "Throttle abuse increases fuel consumption, emissions, and drivetrain stress.",
            "recommendation": "Coach the driver on smoother throttle application during the next trip review.",
        },
    ),
    (
        "aggressive throttle events",
        {
            "code": "AGGRESSIVE_THROTTLE_EVENTS",
            "title": "Aggressive throttle behaviour",
            "severity": "warning",
            "impact": "Frequent aggressive throttle events increase fuel consumption and drivetrain stress.",
            "recommendation": "Monitor driver behaviour during the next trip and provide targeted coaching if events persist.",
        },
    ),
    # Brakes
    (
        "harsh braking events",
        {
            "code": "HARSH_BRAKING_EVENTS",
            "title": "Harsh braking events",
            "severity": "warning",
            "impact": "Frequent harsh braking accelerates pad and disc wear and increases collision risk.",
            "recommendation": "Review following distances and braking technique during the next driver debrief.",
        },
    ),
    (
        "harsh braking pressure",
        {
            "code": "HARSH_BRAKING_PRESSURE",
            "title": "Harsh braking pressure",
            "severity": "warning",
            "impact": "Very high brake pressure indicates emergency-style stops that wear components rapidly.",
            "recommendation": "Inspect brake pads and discs at the next service and review braking thresholds.",
        },
    ),
    (
        "frequent hard braking",
        {
            "code": "FREQUENT_HARD_BRAKING",
            "title": "Frequent hard braking",
            "severity": "warning",
            "impact": "Repeated hard braking degrades brake components faster than scheduled intervals.",
            "recommendation": "Schedule a brake inspection ahead of the next planned service.",
        },
    ),
    # Cooling
    (
        "overheating",
        {
            "code": "OVERHEATING",
            "title": "Overheating",
            "severity": "critical",
            "impact": "Overheating can cause coolant loss, head gasket failure, and warped components.",
            "recommendation": "Stop the vehicle safely, allow the system to cool, and inspect coolant level and hoses immediately.",
        },
    ),
    (
        "elevated coolant temperature",
        {
            "code": "ELEVATED_COOLANT_TEMPERATURE",
            "title": "Elevated coolant temperature",
            "severity": "warning",
            "impact": "Sustained elevated temperature reduces component life and risks escalation to full overheating.",
            "recommendation": "Monitor coolant temperature closely and schedule a cooling system inspection.",
        },
    ),
    (
        "unstable coolant temperature",
        {
            "code": "UNSTABLE_COOLANT_TEMPERATURE",
            "title": "Unstable coolant temperature",
            "severity": "warning",
            "impact": "Temperature instability suggests thermostat, water pump, or sensor issues.",
            "recommendation": "Inspect the cooling system for air locks, pump wear, or thermostat malfunction.",
        },
    ),
    (
        "high thermal load",
        {
            "code": "HIGH_THERMAL_LOAD",
            "title": "High thermal load",
            "severity": "warning",
            "impact": "Sustained high thermal load stresses the radiator and cooling passages.",
            "recommendation": "Review load management and verify cooling system capacity for the duty cycle.",
        },
    ),
    # Transmission
    (
        "high rpm at low speed",
        {
            "code": "HIGH_RPM_LOW_SPEED",
            "title": "High RPM at low speed",
            "severity": "warning",
            "impact": "Drivetrain lugging at high RPM and low speed causes unnecessary wear on transmission and clutch components.",
            "recommendation": "Review gear selection strategy and avoid holding high RPM at low road speeds.",
        },
    ),
    (
        "repeated drivetrain stress",
        {
            "code": "REPEATED_DRIVETRAIN_STRESS",
            "title": "Repeated drivetrain stress",
            "severity": "warning",
            "impact": "Frequent drivetrain stress events accelerate transmission and differential wear.",
            "recommendation": "Schedule a transmission inspection at the next service interval.",
        },
    ),
    # Fuel System
    (
        "poor fuel efficiency",
        {
            "code": "POOR_FUEL_EFFICIENCY",
            "title": "Poor fuel efficiency",
            "severity": "warning",
            "impact": "Reduced efficiency increases operating cost and may indicate injector or filter degradation.",
            "recommendation": "Inspect fuel filter and injectors at the next service interval.",
        },
    ),
    (
        "excessive fuel consumption",
        {
            "code": "EXCESSIVE_FUEL_CONSUMPTION",
            "title": "Excessive fuel consumption",
            "severity": "warning",
            "impact": "High fuel consumption raises operational costs and may signal metering or air-intake issues.",
            "recommendation": "Schedule a fuel system inspection to check for leaks, filter blockage, or injector faults.",
        },
    ),
    (
        "high throttle fuel use",
        {
            "code": "HIGH_THROTTLE_FUEL_USE",
            "title": "High throttle fuel use",
            "severity": "warning",
            "impact": "High throttle combined with high fuel rate indicates inefficient combustion and increased wear.",
            "recommendation": "Review driver throttle discipline and inspect the fuel delivery system.",
        },
    ),
)


def _match_metadata(reason: str) -> dict[str, object] | None:
    """Return the first metadata entry whose prefix matches the reason."""
    for prefix, meta in _REASON_METADATA:
        if reason.startswith(prefix):
            return meta
    return None


def _parse_evidence(reason: str) -> dict[str, object] | None:
    """Extract quantitative evidence from a reason string."""
    evidence: dict[str, object] = {}

    rpm_match = re.search(r"([\d,]+)\s*rpm", reason)
    if rpm_match:
        evidence["rpm"] = int(rpm_match.group(1).replace(",", ""))

    percent_match = re.search(r"([\d.]+)%", reason)
    if percent_match:
        evidence["percent"] = float(percent_match.group(1))

    fraction_match = re.search(r"([\d.]+)% of window", reason)
    if fraction_match:
        evidence["window_fraction"] = float(fraction_match.group(1)) / 100.0

    temp_match = re.search(r"([\d.]+)\s*C", reason)
    if temp_match:
        evidence["temperature_c"] = float(temp_match.group(1))

    stddev_match = re.search(r"stddev ([\d.]+)", reason)
    if stddev_match:
        evidence["stddev_c"] = float(stddev_match.group(1))

    km_match = re.search(r"([\d.]+)\s*km/h", reason)
    if km_match:
        evidence["speed_kmh"] = float(km_match.group(1))

    efficiency_match = re.search(r"([\d.]+)\s*km/L", reason)
    if efficiency_match:
        evidence["efficiency_km_per_l"] = float(efficiency_match.group(1))

    throttle_match = re.search(r"throttle ([\d.]+)%", reason)
    if throttle_match:
        evidence["throttle_percent"] = float(throttle_match.group(1))

    count_match = re.search(r"\((\d+)\)", reason)
    if count_match and "events" in reason:
        evidence["event_count"] = int(count_match.group(1))

    load_match = re.search(r"mean ([\d.]+)%", reason)
    if load_match:
        evidence["mean_load_percent"] = float(load_match.group(1))

    if evidence:
        return evidence
    return None


def _severity_for_score(score: float | None) -> str:
    """Derive a base severity from a subsystem health score."""
    if score is None:
        return "warning"
    if score < 50.0:
        return "critical"
    if score < 75.0:
        return "warning"
    return "info"


def _enrich_reason(
    subsystem: str,
    reason: str,
    subsystem_health: SubsystemHealth | None,
) -> HealthReason:
    """Convert a plain reason string into a structured HealthReason."""
    meta = _match_metadata(reason) or {}
    base_severity = meta.get("severity", "warning")
    score_severity = _severity_for_score(
        subsystem_health.score if subsystem_health else None
    )

    # Promote severity if the subsystem score is poor.
    severity_rank = {"info": 0, "warning": 1, "critical": 2}
    if severity_rank.get(score_severity, 1) > severity_rank.get(base_severity, 1):
        severity = score_severity
    else:
        severity = base_severity

    evidence = _parse_evidence(reason)

    return HealthReason(
        subsystem=subsystem,
        reason=reason,
        code=str(meta.get("code", "")),
        title=str(meta.get("title", "")),
        severity=severity,
        summary=reason,
        evidence=evidence,
        impact=meta.get("impact"),
        recommendation=meta.get("recommendation"),
    )


def flatten_health_reasons(
    health: HealthSnapshot | None,
) -> tuple[HealthReason, ...]:
    """
    Flatten the canonical HealthSnapshot reasons.

    Returns an empty tuple for None (no snapshot yet) or a snapshot
    without reasons. Identical (subsystem, reason) pairs are produced
    once. Each reason is enriched with structured metadata so the
    frontend can render explainable operational intelligence.
    """
    if health is None:
        return ()

    reasons: list[HealthReason] = []
    seen: set[tuple[str, str]] = set()

    for subsystem in _SUBSYSTEM_ORDER:
        attribute = _SUBSYSTEM_ATTRIBUTES[subsystem]
        subsystem_health = getattr(health, attribute, None)
        if subsystem_health is None:
            continue
        for reason in subsystem_health.reasons:
            if not reason:
                continue
            key = (subsystem, reason)
            if key in seen:
                continue
            seen.add(key)
            reasons.append(
                _enrich_reason(
                    subsystem=subsystem,
                    reason=reason,
                    subsystem_health=subsystem_health,
                )
            )

    return tuple(reasons)


__all__ = ["flatten_health_reasons", "SUBSYSTEM_ORDER"]
