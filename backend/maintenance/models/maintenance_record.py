"""
Maintenance Record model.

Represents a completed or scheduled maintenance event
(e.g. oil change, brake pad replacement, tire replacement).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MaintenanceType(str, Enum):
    OIL_CHANGE = "oil_change"
    BRAKE_PAD_REPLACEMENT = "brake_pad_replacement"
    TIRE_REPLACEMENT = "tire_replacement"
    OTHER = "other"


@dataclass
class MaintenanceRecord:
    maintenance_id: str
    vehicle_id: str
    maintenance_type: MaintenanceType
    odometer_km: float
    performed_at: datetime