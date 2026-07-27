from dataclasses import dataclass
from datetime import datetime


@dataclass
class BehaviourEvent:
    vehicle_id: str
    driver_id: str
    trip_id: str

    event_type: str

    started_at: datetime
    ended_at: datetime

    duration_seconds: float
    distance_km: float

    severity: str

    max_speed_excess_kmh: float | None = None
    max_rpm: float | None = None
    max_throttle_percent: float | None = None
    max_braking_intensity: float | None = None