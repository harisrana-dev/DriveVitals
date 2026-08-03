"""
Cooling Maintenance Estimator.

Estimates maintenance needs for the cooling subsystem only.
"""

from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.maintenance.estimators.component_estimator import (
    ComponentEstimator,
)
from backend.maintenance.maintenance_config import ServiceProfile


class CoolingEstimator(ComponentEstimator):
    """
    Purpose:
        Estimate cooling maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses cooling_health) and current odometer.
    Outputs:
        A list of MaintenanceRecommendation objects for the cooling
        system.
    """

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.COOLING

    @property
    def services(self) -> tuple[ServiceProfile, ...]:
        return self._config.cooling_services

    @property
    def component(self) -> str:
        return "cooling"
