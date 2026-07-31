"""
Maintenance estimator interface.

Each estimator is responsible for exactly ONE component and derives a
MaintenanceRecommendation from a HealthSnapshot.
"""

from abc import ABC, abstractmethod

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)


class MaintenanceEstimator(ABC):
    """
    Purpose:
        Interface implemented by every component maintenance estimator.
    Inputs:
        A HealthSnapshot.
    Outputs:
        A MaintenanceRecommendation for a single component.
    TODO:
        Decide whether estimators also need historical maintenance
        context (e.g. last service odometer).
    """

    @property
    @abstractmethod
    def component(self) -> str:
        """The component this estimator evaluates."""
        raise NotImplementedError

    @abstractmethod
    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> MaintenanceRecommendation:
        """Estimate maintenance needs for this estimator's component."""
        raise NotImplementedError


__all__ = ["MaintenanceEstimator"]
