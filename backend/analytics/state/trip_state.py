"""
Trip Analytics State.

Represents the analytical state of a currently active or completed
trip. Updated by the trip analyzer; carries aggregated metrics,
event counts, and assessment summaries. Contains no calculation
logic.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TripAnalyticsState:
    trip_id: str
    vehicle_id: str
    driver_id: str

    trip_status: str = ""

    distance_km: float = 0.0
    duration_seconds: float = 0.0

    average_speed_kmh: float = 0.0
    maximum_speed_kmh: float = 0.0

    fuel_consumed_liters: float = 0.0
    fuel_efficiency_km_per_liter: float = 0.0

    harsh_acceleration_count: int = 0
    harsh_braking_count: int = 0
    overspeed_event_count: int = 0

    driver_behavior: str = ""
    vehicle_health: str = ""

    trip_score: float = 0.0

    last_updated: datetime | None = None
