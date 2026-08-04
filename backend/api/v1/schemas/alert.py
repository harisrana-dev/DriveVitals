from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    vehicle_id: str
    driver_id: str | None
    trip_id: str | None
    alert_type: str
    severity: str
    status: str
    acknowledged: bool
    created_at: datetime
    resolved_at: datetime | None
