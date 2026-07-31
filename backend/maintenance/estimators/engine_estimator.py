"""
Engine Maintenance Estimator.

Estimates maintenance needs for the engine component only.
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


class EngineEstimator(MaintenanceEstimator):
    """
    Purpose:
        Estimate engine maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses engine_health).
    Outputs:
        A MaintenanceRecommendation for the engine component.
    TODO:
        Define engine-specific estimation rules once scoring is
        defined.
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
        return "engine"

    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> MaintenanceRecommendation:
        """
        Estimate engine maintenance needs.

        TODO: Implement. Uses health_snapshot.engine_health.
        """
        raise NotImplementedError
