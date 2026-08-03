"""
Fuel System Maintenance Estimator.

Estimates maintenance needs for the fuel system subsystem only.
"""

from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.maintenance.estimators.component_estimator import (
    ComponentEstimator,
)
from backend.maintenance.maintenance_config import ServiceProfile


class FuelSystemEstimator(ComponentEstimator):
    """
    Purpose:
        Estimate fuel system maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses fuel_system_health) and current odometer.
    Outputs:
        A list of MaintenanceRecommendation objects for the fuel
        system.
    """

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.FUEL_SYSTEM

    @property
    def services(self) -> tuple[ServiceProfile, ...]:
        return self._config.fuel_system_services

    @property
    def component(self) -> str:
        return "fuel_system"
