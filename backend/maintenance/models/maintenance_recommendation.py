"""
Maintenance Recommendation model.

Immutable recommendation for one maintenance service on one vehicle,
produced by a maintenance estimator. Contains no estimation logic.

    MaintenancePriority  how soon the work must happen
    MaintenanceSeverity  how bad the subsystem condition is right now
    remaining_km         estimated distance until the work is due
    reason               why the work is being recommended
    recommended_action   what should be done
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.maintenance.models.maintenance_type import MaintenanceType


class MaintenancePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MaintenanceSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass(frozen=True, slots=True)
class MaintenanceRecommendation:
    """
    Purpose:
        Describe one upcoming maintenance service for one component.
    Inputs:
        Produced by a maintenance estimator from a HealthSnapshot.
    Outputs:
        Consumed by the MaintenanceService and maintenance alert
        generators.
    """

    vehicle_id: str
    component: str
    maintenance_type: MaintenanceType
    priority: MaintenancePriority
    severity: MaintenanceSeverity
    remaining_km: float
    reason: str
    recommended_action: str
    estimated_cost: float | None = None
    estimated_due_date: datetime | None = None


__all__ = [
    "MaintenancePriority",
    "MaintenanceSeverity",
    "MaintenanceRecommendation",
]
