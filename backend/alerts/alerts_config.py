"""
Alert configuration.

Central home for every constant used by the Alert subsystem:

    * duplicate suppression cooldown
    * health status -> alert rules
    * maintenance priority -> alert severity mapping
    * telemetry threshold values and severities
    * trip behaviour thresholds and severities
    * shared sorting rank and vocabulary constants

Constants must never be scattered across alert modules. New knobs are
introduced here first and consumed through AlertConfig.
"""

from dataclasses import dataclass, field

from backend.alerts.models.fleet_alert import AlertSeverity
from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenancePriority,
)

# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

# Sort rank so alerts order by urgency: CRITICAL first, INFO last.
SEVERITY_RANK: dict[AlertSeverity, int] = {
    AlertSeverity.CRITICAL: 0,
    AlertSeverity.HIGH: 1,
    AlertSeverity.MEDIUM: 2,
    AlertSeverity.LOW: 3,
    AlertSeverity.INFO: 4,
}

# ---------------------------------------------------------------------------
# Behaviour event vocabulary
# ---------------------------------------------------------------------------

# Mirrors the event types produced by the behaviour tracker. Kept local
# so the Alert subsystem does not depend on Driver Statistics.
EVENT_TYPE_HARSH_BRAKING = "harsh_braking"
EVENT_TYPE_AGGRESSIVE_THROTTLE = "aggressive_throttle"
EVENT_TYPE_SPEEDING = "speeding"

EVENT_SEVERITY_SEVERE = "severe"

# ---------------------------------------------------------------------------
# Alert identifiers (deduplication keys are derived from these)
# ---------------------------------------------------------------------------

TELEMETRY_ENGINE_OVERHEATING = "telemetry_engine_overheating"
TELEMETRY_COOLANT_CRITICAL = "telemetry_coolant_critical"
TELEMETRY_FUEL_CRITICAL = "telemetry_fuel_critical"
TELEMETRY_RPM_REDLINE = "telemetry_rpm_redline"

TRIP_OVERSPEEDING = "trip_overspeeding"
TRIP_REPEATED_HARSH_BRAKING = "trip_repeated_harsh_braking"
TRIP_REPEATED_HARSH_ACCELERATION = "trip_repeated_harsh_acceleration"
TRIP_AGGRESSIVE_DRIVING = "trip_aggressive_driving"
TRIP_UNSAFE = "trip_unsafe"

# ---------------------------------------------------------------------------
# Health generator
# ---------------------------------------------------------------------------

_HEALTH_STATUS_SEVERITY: dict[HealthStatus, AlertSeverity] = {
    HealthStatus.WARNING: AlertSeverity.HIGH,
    HealthStatus.CRITICAL: AlertSeverity.CRITICAL,
}


@dataclass(frozen=True, slots=True)
class HealthAlertConfig:
    """
    Which health statuses surface as alerts and how each status maps to
    an alert severity.

    Only subsystems whose status is present in alert_statuses emit an
    alert, so the generator is quiet while a vehicle is healthy.
    """

    alert_statuses: frozenset[HealthStatus] = frozenset(
        {HealthStatus.CRITICAL}
    )
    status_severity: dict[HealthStatus, AlertSeverity] = field(
        default_factory=lambda: dict(_HEALTH_STATUS_SEVERITY)
    )


# ---------------------------------------------------------------------------
# Maintenance generator
# ---------------------------------------------------------------------------

_PRIORITY_SEVERITY: dict[MaintenancePriority, AlertSeverity] = {
    MaintenancePriority.CRITICAL: AlertSeverity.CRITICAL,
    MaintenancePriority.HIGH: AlertSeverity.HIGH,
    MaintenancePriority.MEDIUM: AlertSeverity.MEDIUM,
    MaintenancePriority.LOW: AlertSeverity.LOW,
}


@dataclass(frozen=True, slots=True)
class MaintenanceAlertConfig:
    """
    Map a maintenance recommendation priority to an alert severity.

    The recommendation already decided urgency; the alert layer only
    translates it.
    """

    priority_severity: dict[MaintenancePriority, AlertSeverity] = field(
        default_factory=lambda: dict(_PRIORITY_SEVERITY)
    )


# ---------------------------------------------------------------------------
# Telemetry generator
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TelemetryAlertConfig:
    """
    Live telemetry thresholds and their alert severities.

    Temperature limits mirror the Vehicle Health engine thresholds so the
    two layers classify the same readings consistently.
    """

    engine_overheat_temp_c: float = 105.0
    engine_overheat_severity: AlertSeverity = AlertSeverity.CRITICAL

    coolant_critical_temp_c: float = 100.0
    coolant_critical_severity: AlertSeverity = AlertSeverity.CRITICAL

    fuel_critical_percent: float = 15.0
    fuel_critical_severity: AlertSeverity = AlertSeverity.CRITICAL

    redline_rpm: float = 6200.0
    redline_severity: AlertSeverity = AlertSeverity.HIGH


# ---------------------------------------------------------------------------
# Trip generator
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TripAlertConfig:
    """
    Trip behaviour thresholds and their alert severities.

    Event-driven alerts fire from behaviour events collected on a trip;
    the counts are compared against these minimums.
    """

    overspeed_min_events: int = 1
    overspeed_severity: AlertSeverity = AlertSeverity.MEDIUM

    repeated_event_min: int = 3
    repeated_harsh_braking_severity: AlertSeverity = AlertSeverity.MEDIUM
    repeated_harsh_acceleration_severity: AlertSeverity = (
        AlertSeverity.MEDIUM
    )

    aggressive_driving_min_severe_events: int = 1
    aggressive_driving_severity: AlertSeverity = AlertSeverity.HIGH

    unsafe_trip_min_events: int = 5
    unsafe_trip_severity: AlertSeverity = AlertSeverity.CRITICAL


# ---------------------------------------------------------------------------
# Aggregate configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AlertConfig:
    """Aggregate configuration for the Alert subsystem."""

    duplicate_cooldown_seconds: float = 300.0
    health: HealthAlertConfig = HealthAlertConfig()
    maintenance: MaintenanceAlertConfig = MaintenanceAlertConfig()
    telemetry: TelemetryAlertConfig = TelemetryAlertConfig()
    trip: TripAlertConfig = TripAlertConfig()


DEFAULT_ALERT_CONFIG = AlertConfig()


__all__ = [
    "SEVERITY_RANK",
    "EVENT_TYPE_HARSH_BRAKING",
    "EVENT_TYPE_AGGRESSIVE_THROTTLE",
    "EVENT_TYPE_SPEEDING",
    "EVENT_SEVERITY_SEVERE",
    "TELEMETRY_ENGINE_OVERHEATING",
    "TELEMETRY_COOLANT_CRITICAL",
    "TELEMETRY_FUEL_CRITICAL",
    "TELEMETRY_RPM_REDLINE",
    "TRIP_OVERSPEEDING",
    "TRIP_REPEATED_HARSH_BRAKING",
    "TRIP_REPEATED_HARSH_ACCELERATION",
    "TRIP_AGGRESSIVE_DRIVING",
    "TRIP_UNSAFE",
    "HealthAlertConfig",
    "MaintenanceAlertConfig",
    "TelemetryAlertConfig",
    "TripAlertConfig",
    "AlertConfig",
    "DEFAULT_ALERT_CONFIG",
]
