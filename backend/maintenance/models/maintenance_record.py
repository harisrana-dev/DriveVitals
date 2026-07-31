"""
Maintenance Record model.

Represents a completed or scheduled maintenance event
(e.g. oil change, brake pad replacement, tire replacement).
"""

from dataclasses import dataclass
from datetime import datetime

from backend.maintenance.models.maintenance_type import MaintenanceType


@dataclass
class MaintenanceRecord:
    maintenance_id: str
    vehicle_id: str
    maintenance_type: MaintenanceType
    odometer_km: float
    performed_at: datetime