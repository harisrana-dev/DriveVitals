"""
Maintenance estimator interface.

Each estimator is responsible for exactly ONE subsystem and derives a
list of MaintenanceRecommendation objects from a HealthSnapshot, the
vehicle's odometer and the latest telemetry sample.
"""

from abc import ABC, abstractmethod

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class MaintenanceEstimator(ABC):
    """
    Purpose:
        Interface implemented by every subsystem maintenance estimator.
    Inputs:
        A HealthSnapshot, the current odometer reading and the latest
        telemetry sample.
    Outputs:
        A list of MaintenanceRecommendation objects for one subsystem.
    """

    @property
    @abstractmethod
    def component(self) -> str:
        """The subsystem this estimator evaluates."""
        raise NotImplementedError

    @abstractmethod
    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
        odometer_km: float,
        telemetry_sample: TelemetrySample | None = None,
    ) -> list[MaintenanceRecommendation]:
        """Estimate maintenance needs for this estimator's subsystem."""
        raise NotImplementedError


__all__ = ["MaintenanceEstimator"]
