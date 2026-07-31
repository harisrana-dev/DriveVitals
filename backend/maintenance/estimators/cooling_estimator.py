"""
Cooling Maintenance Estimator.

Estimates maintenance needs for the cooling component only.
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


class CoolingEstimator(MaintenanceEstimator):
    """
    Purpose:
        Estimate cooling maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses cooling_health).
    Outputs:
        A MaintenanceRecommendation for the cooling component.
    TODO:
        Define cooling-specific estimation rules once scoring is
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
        return "cooling"

    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> MaintenanceRecommendation:
        """
        Estimate cooling maintenance needs.

        TODO: Implement. Uses health_snapshot.cooling_health.
        """
        raise NotImplementedError
