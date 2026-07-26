"""
Driver Analytics State.

Represents the current analytical state of a driver. Updated by the
driver behavior analyzer; carries classification results and
accumulated event counts for a rolling analysis window. Contains no
classification logic itself.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DriverAnalyticsState:
    driver_id: str
    vehicle_id: str

    behavior_classification: str = ""
    behavior_confidence: float = 0.0

    driving_score: float = 0.0

    aggressive_acceleration_count: int = 0
    harsh_braking_count: int = 0
    overspeed_event_count: int = 0

    average_speed_kmh: float = 0.0
    average_throttle_percent: float = 0.0
    average_brake_pressure: float = 0.0

    fuel_efficiency_km_per_liter: float = 0.0

    behavior_reasons: list[str] = field(default_factory=list)

    last_updated: datetime | None = None
