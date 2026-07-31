"""
Brake Maintenance Estimator.

Estimates maintenance needs for the brake subsystem only.

Aggressive braking history is already interpreted by Vehicle Health and
carried in the brake health score (harsh-braking events reduce it), so
this estimator reads the brake health score rather than re-consuming
telemetry history.
"""

from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.maintenance.estimators.component_estimator import (
    ComponentEstimator,
)
from backend.maintenance.maintenance_config import ServiceProfile


class BrakeEstimator(ComponentEstimator):
    """
    Purpose:
        Estimate brake maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses brake_health) and current odometer.
    Outputs:
        A list of MaintenanceRecommendation objects for the brakes.
    """

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.BRAKES

    @property
    def services(self) -> tuple[ServiceProfile, ...]:
        return self._config.brake_services

    @property
    def component(self) -> str:
        return "brakes"
