"""
Brake Maintenance Estimator.

Estimates maintenance needs for the brake component only.
"""

from collections.abc import Mapping

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.maintenance.estimators.maintenance_estimator import (
    MaintenanceEstimator,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)


class BrakeEstimator(MaintenanceEstimator):
    """
    Purpose:
        Estimate brake maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses brake_health).
    Outputs:
        A MaintenanceRecommendation for the brake component.
    TODO:
        Define brake-specific estimation rules once scoring is defined.
    """

    def __init__(
        self,
        *,
        thresholds: Mapping[str, float] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        thresholds:
            Future estimator-specific thresholds. Intentionally left
            undefined in this milestone so no values are guessed.
        """
        self._thresholds = thresholds

    @property
    def component(self) -> str:
        return "brakes"

    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> MaintenanceRecommendation:
        """
        Estimate brake maintenance needs.

        TODO: Implement. Uses health_snapshot.brake_health.
        """
        raise NotImplementedError
