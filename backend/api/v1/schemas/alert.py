from datetime import datetime
from typing import Any

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
    acknowledged_at: datetime | None
    created_at: datetime
    last_triggered_at: datetime | None
    resolved_at: datetime | None
    condition: str | None
    category: str | None
    message: str | None
    evidence: dict[str, Any] | None
    source: str
