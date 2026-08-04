from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: str
    registration_number: str
    vin: str
    manufacturer: str
    model: str
    year: int
    fuel_type: str
    status: str
    created_at: datetime
    updated_at: datetime
