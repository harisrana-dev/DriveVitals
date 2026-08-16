from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    maintenance_id: str
    vehicle_id: str
    maintenance_type: str
    priority: str
    status: str
    due_odometer_km: float | None
    due_date: datetime | None
    component: str | None
    reason: str | None
    recommended_action: str | None
    estimated_cost: float | None
    completed_odometer_km: float | None
    created_at: datetime
    completed_at: datetime | None


class MaintenanceCompleteRequest(BaseModel):
    completed_odometer_km: float | None = None
