"""
Maintenance estimation rules.

Pure, deterministic calculations shared by every maintenance estimator.
No estimator re-implements these — they are the single source of truth
for how health scores, odometers and distances turn into
recommendations.
"""

from datetime import datetime, timedelta

from backend.maintenance.maintenance_config import (
    PriorityThresholds,
    SeverityThresholds,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenancePriority,
    MaintenanceSeverity,
)

# Sort rank so the MaintenanceService can order by urgency.
PRIORITY_RANK: dict[MaintenancePriority, int] = {
    MaintenancePriority.CRITICAL: 0,
    MaintenancePriority.HIGH: 1,
    MaintenancePriority.MEDIUM: 2,
    MaintenancePriority.LOW: 3,
}


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a value into [low, high]."""
    return min(high, max(low, value))


def health_factor(score: float) -> float:
    """
    Map a subsystem health score in [0, 100] to a remaining-life factor
    in [0, 1].

    A fully healthy subsystem (100) keeps its full service interval; a
    degraded one gets proportionally less. This is what makes health
    deterioration pull services closer.
    """
    return clamp(score / 100.0, 0.0, 1.0)


def interval_remaining_km(odometer_km: float, interval_km: float) -> float:
    """
    Distance until the next service for an interval-based service, based
    on the odometer phase within the interval.

    With no maintenance history available, the odometer position modulo
    the service interval is used to estimate how much of the current
    interval has already been consumed. An exact multiple of the interval
    is treated as a freshly completed service.
    """
    if odometer_km < 0.0:
        raise ValueError("odometer_km must be non-negative")
    if interval_km <= 0.0:
        raise ValueError("interval_km must be positive")
    progress_km = odometer_km % interval_km
    return interval_km - progress_km


def priority_for(
    remaining_km: float,
    thresholds: PriorityThresholds,
) -> MaintenancePriority:
    """Map a remaining distance to a MaintenancePriority."""
    if remaining_km <= thresholds.high_min_km:
        return MaintenancePriority.CRITICAL
    if remaining_km <= thresholds.medium_min_km:
        return MaintenancePriority.HIGH
    if remaining_km <= thresholds.low_min_km:
        return MaintenancePriority.MEDIUM
    return MaintenancePriority.LOW


def severity_for(
    score: float,
    thresholds: SeverityThresholds,
) -> MaintenanceSeverity:
    """Map a subsystem health score to a MaintenanceSeverity."""
    if score >= thresholds.minor_min_score:
        return MaintenanceSeverity.MINOR
    if score >= thresholds.moderate_min_score:
        return MaintenanceSeverity.MODERATE
    return MaintenanceSeverity.SEVERE


def estimated_due_date(
    *,
    timestamp: datetime,
    remaining_km: float,
    daily_distance_km: float,
) -> datetime:
    """Project a due date from a remaining distance and daily usage."""
    if daily_distance_km <= 0.0:
        raise ValueError("daily_distance_km must be positive")
    if remaining_km < 0.0:
        raise ValueError("remaining_km must be non-negative")
    days_until_due = remaining_km / daily_distance_km
    return timestamp + timedelta(days=days_until_due)


__all__ = [
    "PRIORITY_RANK",
    "clamp",
    "health_factor",
    "interval_remaining_km",
    "priority_for",
    "severity_for",
    "estimated_due_date",
]
