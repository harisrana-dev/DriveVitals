"""
Fuel System Maintenance Estimator.

Estimates maintenance needs for the fuel system component only.
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


class FuelSystemEstimator(MaintenanceEstimator):
    """
    Purpose:
        Estimate fuel system maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses fuel_system_health).
    Outputs:
        A MaintenanceRecommendation for the fuel system component.
    TODO:
        Define fuel-system-specific estimation rules once scoring is
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
        return "fuel_system"

    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> MaintenanceRecommendation:
        """
        Estimate fuel system maintenance needs.

        TODO: Implement. Uses health_snapshot.fuel_system_health.
        """
        raise NotImplementedError
