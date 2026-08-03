"""
SubsystemHealth model.

Result shape for a single subsystem health assessment produced by a
dedicated analyzer. Contains no scoring or calculation logic — only
the data.

One SubsystemHealth is produced per analyzed subsystem and is later
combined into a HealthSnapshot by the VehicleHealthEngine.
"""

from dataclasses import dataclass
from enum import Enum


class Subsystem(str, Enum):
    ENGINE = "engine"
    COOLING = "cooling"
    TRANSMISSION = "transmission"
    BRAKES = "brakes"
    FUEL_SYSTEM = "fuel_system"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SubsystemHealth:
    """
    Purpose:
        Describe the assessed health of one vehicle subsystem.
    Inputs:
        Produced by a single subsystem health analyzer.
    Outputs:
        Consumed by the VehicleHealthEngine when assembling a
        HealthSnapshot.
    """

    subsystem: Subsystem
    score: float
    status: HealthStatus
    reasons: tuple[str, ...] = ()
