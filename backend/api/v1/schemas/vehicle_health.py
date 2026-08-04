from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleHealthRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: str
    overall_health_score: float
    engine_health: float
    brake_health: float
    transmission_health: float
    cooling_health: float
    fuel_system_health: float
    last_updated: datetime
