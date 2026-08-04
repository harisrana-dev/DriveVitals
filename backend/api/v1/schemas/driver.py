from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    driver_id: str
    first_name: str
    last_name: str
    license_number: str
    employment_status: str
    created_at: datetime
    updated_at: datetime
