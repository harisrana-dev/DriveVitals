"""
HealthSnapshot model.

Immutable, combined vehicle health assessment produced by the
VehicleHealthEngine. Aggregates the result of every subsystem analyzer
into a single snapshot. Contains no health-calculation logic.
"""

from dataclasses import dataclass
from datetime import datetime

from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
    SubsystemHealth,
)


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    """
    Purpose:
        Immutable point-in-time health assessment for one vehicle.
    Inputs:
        Assembled by the VehicleHealthEngine from subsystem results.
    Outputs:
        Consumed by maintenance estimators and health alert
        generators.
    """

    vehicle_id: str
    timestamp: datetime
    overall_health_score: float
    overall_status: HealthStatus
    engine_health: SubsystemHealth
    cooling_health: SubsystemHealth
    transmission_health: SubsystemHealth
    brake_health: SubsystemHealth
    fuel_system_health: SubsystemHealth
    driver_id: str | None = None
    trip_id: str | None = None
