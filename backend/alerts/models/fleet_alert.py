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
        Alert details live in the message; no payload field is carried
        so the model stays minimal.
    """

    alert_id: str
    vehicle_id: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    created_at: datetime
    driver_id: str | None = None
    trip_id: str | None = None
