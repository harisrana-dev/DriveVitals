"""
Maintenance Recommendation model.

Immutable recommendation for one vehicle component produced by a
maintenance estimator. Contains no estimation logic.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MaintenancePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class MaintenanceRecommendation:
    """
    Purpose:
        Describe a maintenance recommendation for one component.
    Inputs:
        Produced by a maintenance estimator from a HealthSnapshot.
    Outputs:
        Consumed by the MaintenanceService and maintenance alert
        generators.
    TODO:
        Decide the units for remaining_life and whether component
        should be an enum.
    """

    vehicle_id: str
    component: str
    remaining_life: float
    remaining_distance: float
    priority: MaintenancePriority
    recommendation: str
    due_date: datetime | None = None
