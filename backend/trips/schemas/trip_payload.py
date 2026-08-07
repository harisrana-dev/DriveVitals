from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TripSnapshot:
    trip_id: str
    vehicle_id: str
    driver_id: str
    vehicle_name: str | None
    driver_name: str | None
    route_id: str
    route_type: str
    distance_km: float
    duration_seconds: float
    average_speed_kmh: float
    maximum_speed_kmh: float
    fuel_consumed_liters: float
    average_fuel_rate_lph: float
    safety_score: float
    overall_grade: str
    started_at: datetime | None
    completed_at: datetime | None
    speeding_event_count: int
    speeding_duration_seconds: float
    harsh_braking_count: int
    aggressive_throttle_event_count: int
    aggressive_throttle_duration_seconds: float
    high_rpm_event_count: int
    high_rpm_duration_seconds: float
    severe_event_count: int
    moderate_event_count: int
    minor_event_count: int
    overall_severity: str
    events: tuple[dict, ...]

    route_name: str | None = None


@dataclass(frozen=True, slots=True)
class TripsSnapshot:
    timestamp: datetime
    trips: tuple[TripSnapshot, ...]
    total_trips: int
    total_distance_km: float
    average_safety_score: float
    total_fuel_consumed_liters: float
