"""
Fleet Alert model.

Immutable alert produced by the Alert Engine. Contains no alert
generation logic.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    MAINTENANCE = "maintenance"
    TELEMETRY = "telemetry"
    HEALTH = "health"
    TRIP = "trip"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(str, Enum):
    """
    Canonical operational category for an alert.

    Categories are assigned by the backend (via the generators) so the
    frontend never has to guess a category from the alert id or type.
    """

    SAFETY_DRIVING = "safety_driving"
    VEHICLE_HEALTH = "vehicle_health"
    COOLING = "cooling"
    FUEL = "fuel"
    ENGINE = "engine"
    ELECTRICAL = "electrical"
    TRANSMISSION = "transmission"
    BRAKES = "brakes"
    MAINTENANCE = "maintenance"
    TRIP = "trip"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class FleetAlert:
    """
    Purpose:
        Represent one alert generated for the fleet.
    Inputs:
        Produced by an alert generator.
    Outputs:
        Consumed by persistence and, in the future, by dashboard APIs.
    Note:
        The model carries a canonical ``condition`` key (the alert id is
        the canonical form) plus an explicit ``category`` and an optional
        ``evidence`` snapshot. Generators are responsible for filling
        these; consumers never derive meaning from the message string.
    """

    alert_id: str
    vehicle_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    created_at: datetime
    driver_id: str | None = None
    trip_id: str | None = None
    condition: str | None = None
    category: AlertCategory = AlertCategory.OTHER
    evidence: dict | None = None
    source: str = "alert_engine"
