from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DriverStatisticsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    driver_id: str
    total_trips: int
    total_distance_km: float
    total_driving_time_seconds: int
    average_trip_score: float
    fuel_efficiency: float
    speeding_events: int
    harsh_braking_events: int
    aggressive_throttle_events: int
    high_rpm_events: int
    safety_score: float
    aggression_score: float
    efficiency_score: float
    last_updated: datetime
