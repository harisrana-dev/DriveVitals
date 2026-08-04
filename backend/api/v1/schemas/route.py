from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    name: str
    route_type: str
    origin: str
    destination: str
    estimated_distance_km: float
    created_at: datetime
    updated_at: datetime
