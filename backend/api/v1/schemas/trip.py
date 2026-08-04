from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TripRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trip_id: str
    vehicle_id: str
    driver_id: str
    route_id: str
    start_time: datetime
    end_time: datetime | None
    distance_km: float | None
    duration_seconds: int | None
    fuel_used_liters: float | None
    average_speed_kmh: float | None
    maximum_speed_kmh: float | None
    trip_score: float | None
    status: str
