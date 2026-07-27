from dataclasses import dataclass


@dataclass(frozen=True)
class DriverBehaviourSummary:
    """
    Aggregated driver behaviour for one completed trip or analysis period.
    """

    vehicle_id: str
    driver_id: str
    trip_id: str

    total_distance_km: float

    speeding_event_count: int
    speeding_duration_seconds: float
    speeding_distance_km: float
    maximum_speed_excess_kmh: float

    harsh_braking_count: int

    aggressive_throttle_event_count: int
    aggressive_throttle_duration_seconds: float

    high_rpm_event_count: int
    high_rpm_duration_seconds: float

    severe_event_count: int
    moderate_event_count: int
    minor_event_count: int

    overall_severity: str