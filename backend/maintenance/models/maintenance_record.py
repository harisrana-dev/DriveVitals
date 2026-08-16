"""
Maintenance Record model.

Represents a completed or scheduled maintenance event
(e.g. oil change, brake pad replacement, tire replacement).
"""

from dataclasses import dataclass
from datetime import datetime

from backend.maintenance.models.maintenance_type import MaintenanceType
from backend.maintenance.models.maintenance_recommendation import (
    MaintenancePriority,
)


@dataclass
class MaintenanceRecord:
    maintenance_id: str
    vehicle_id: str
    maintenance_type: MaintenanceType
    odometer_km: float
    performed_at: datetime
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    component: str | None = None
    reason: str | None = None
    recommended_action: str | None = None
    estimated_cost: float | None = None