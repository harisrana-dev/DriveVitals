"""Vehicle health models."""

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)

__all__ = [
    "HealthSnapshot",
    "Subsystem",
    "SubsystemHealth",
]
