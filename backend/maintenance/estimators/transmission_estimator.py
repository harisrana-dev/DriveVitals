"""
Transmission Maintenance Estimator.

Estimates maintenance needs for the transmission subsystem only.
"""

from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.maintenance.estimators.component_estimator import (
    ComponentEstimator,
)
from backend.maintenance.maintenance_config import ServiceProfile


class TransmissionEstimator(ComponentEstimator):
    """
    Purpose:
        Estimate transmission maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses transmission_health) and current odometer.
    Outputs:
        A list of MaintenanceRecommendation objects for the
        transmission.
    """

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.TRANSMISSION

    @property
    def services(self) -> tuple[ServiceProfile, ...]:
        return self._config.transmission_services

    @property
    def component(self) -> str:
        return "transmission"
