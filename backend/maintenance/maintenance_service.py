"""
Maintenance Service.

Coordinates all maintenance estimators and produces MaintenanceRecord
objects ready for persistence. This service never writes to the
database — persistence remains the responsibility of PersistenceService.

    HealthSnapshot
            ↓
    Component Estimators
            ↓
    MaintenanceRecommendations
            ↓
    MaintenanceRecords (for persistence)
"""

from collections.abc import Sequence

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.maintenance.estimators.maintenance_estimator import (
    MaintenanceEstimator,
)
from backend.maintenance.models.maintenance_record import (
    MaintenanceRecord,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)


class MaintenanceService:
    """
    Purpose:
        Coordinate component estimators and build persistable records.
    Inputs:
        HealthSnapshot.
    Outputs:
        MaintenanceRecommendation objects and, when requested,
        MaintenanceRecord objects ready for persistence.
    TODO:
        Decide whether the service needs vehicle context (e.g. current
        odometer) to populate maintenance records.
    """

    def __init__(
        self,
        *,
        estimators: Sequence[MaintenanceEstimator],
    ) -> None:
        self._estimators = tuple(estimators)

    def estimate_maintenance(
        self,
        *,
        health_snapshot: HealthSnapshot,
    ) -> tuple[MaintenanceRecommendation, ...]:
        """
        Run every component estimator for a health snapshot.

        TODO: Implement. Delegates to each registered estimator.
        """
        raise NotImplementedError

    def build_records(
        self,
        *,
        recommendations: Sequence[MaintenanceRecommendation],
    ) -> tuple[MaintenanceRecord, ...]:
        """
        Convert recommendations into MaintenanceRecord objects ready
        for persistence. Does NOT write to the database.

        TODO: Implement. Map recommendations onto the existing
        MaintenanceRecord model.
        """
        raise NotImplementedError

    @property
    def estimators(self) -> tuple[MaintenanceEstimator, ...]:
        """Estimators registered with this service."""
        return self._estimators
