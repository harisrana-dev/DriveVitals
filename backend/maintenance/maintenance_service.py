"""
Maintenance Service.

Coordinates all maintenance estimators and produces immutable
MaintenanceRecommendation objects. The service never writes to the
database — persistence remains the responsibility of PersistenceService.

    HealthSnapshot + Vehicle + Telemetry
                    ↓
        Component Estimators
                    ↓
        MaintenanceRecommendations
                    ↓
        MaintenanceRecords (for persistence)
"""

from collections.abc import Sequence
import logging

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.fleet.models.vehicle import Vehicle
from backend.maintenance.estimation.rules import PRIORITY_RANK
from backend.maintenance.estimators.maintenance_estimator import (
    MaintenanceEstimator,
)
from backend.maintenance.maintenance_config import (
    DEFAULT_MAINTENANCE_CONFIG,
    MaintenanceConfig,
)
from backend.maintenance.models.maintenance_record import (
    MaintenanceRecord,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample

logger = logging.getLogger(__name__)


class MaintenanceService:
    """
    Purpose:
        Orchestrate subsystem estimators into a sorted set of
        maintenance recommendations.
    Inputs:
        A HealthSnapshot, the vehicle and its latest telemetry sample.
    Outputs:
        Immutable MaintenanceRecommendation objects and, when
        requested, MaintenanceRecord objects ready for persistence.
    """

    def __init__(
        self,
        *,
        estimators: Sequence[MaintenanceEstimator],
        config: MaintenanceConfig | None = None,
    ) -> None:
        if not estimators:
            raise ValueError("at least one maintenance estimator is required")

        components = [estimator.component for estimator in estimators]
        if len(set(components)) != len(components):
            raise ValueError(
                "each estimator must evaluate a distinct component"
            )

        self._estimators = tuple(estimators)
        self._config = (
            config if config is not None else DEFAULT_MAINTENANCE_CONFIG
        )

    def estimate_maintenance(
        self,
        *,
        health_snapshot: HealthSnapshot,
        vehicle: Vehicle,
        telemetry_sample: TelemetrySample | None = None,
        odometer_km: float | None = None,
    ) -> tuple[MaintenanceRecommendation, ...]:
        """
        Run every component estimator and return the merged
        recommendations, sorted by priority and urgency.
        """
        self._validate_inputs(
            health_snapshot=health_snapshot,
            vehicle=vehicle,
            telemetry_sample=telemetry_sample,
        )
        odometer = (
            vehicle.odometer_km if odometer_km is None else odometer_km
        )
        if odometer < 0.0:
            raise ValueError("odometer_km must be non-negative")

        recommendations = [
            recommendation
            for estimator in self._estimators
            for recommendation in estimator.estimate(
                health_snapshot=health_snapshot,
                odometer_km=odometer,
                telemetry_sample=telemetry_sample,
            )
        ]
        recommendations.sort(
            key=self._recommendation_sort_key,
        )
        logger.debug(
            "maintenance estimation for vehicle %s: %d recommendations",
            vehicle.vehicle_id,
            len(recommendations),
        )
        return tuple(recommendations)

    def build_records(
        self,
        *,
        recommendations: Sequence[MaintenanceRecommendation],
        odometer_km: float,
    ) -> tuple[MaintenanceRecord, ...]:
        """
        Convert recommendations into MaintenanceRecord objects ready
        for persistence. Does NOT write to the database.

        Each record captures the projected service point: the odometer
        reading at which the work is due and its scheduled date.

        The maintenance identity is ``{vehicle_id}:{maintenance_type}``
        so repeated estimations for the same service update the same
        row rather than creating duplicates as the odometer advances.
        """
        if odometer_km < 0.0:
            raise ValueError("odometer_km must be non-negative")

        records: list[MaintenanceRecord] = []
        seen_types: set[str] = set()
        for recommendation in recommendations:
            if recommendation.estimated_due_date is None:
                raise ValueError(
                    "cannot build a record without an estimated due date"
                )
            projected_odometer = (
                odometer_km + recommendation.remaining_km
            )
            identity = (
                f"{recommendation.vehicle_id}:"
                f"{recommendation.maintenance_type.value}"
            )
            if identity in seen_types:
                continue
            seen_types.add(identity)
            records.append(
                MaintenanceRecord(
                    maintenance_id=identity,
                    vehicle_id=recommendation.vehicle_id,
                    maintenance_type=recommendation.maintenance_type,
                    odometer_km=projected_odometer,
                    performed_at=recommendation.estimated_due_date,
                    priority=recommendation.priority,
                    component=recommendation.component,
                    reason=recommendation.reason,
                    recommended_action=recommendation.recommended_action,
                    estimated_cost=recommendation.estimated_cost,
                )
            )
        return tuple(records)

    @staticmethod
    def _validate_inputs(
        *,
        health_snapshot: HealthSnapshot,
        vehicle: Vehicle,
        telemetry_sample: TelemetrySample | None,
    ) -> None:
        if health_snapshot.vehicle_id != vehicle.vehicle_id:
            raise ValueError(
                "health snapshot and vehicle belong to different "
                f"vehicles ('{health_snapshot.vehicle_id}' vs "
                f"'{vehicle.vehicle_id}')"
            )
        if (
            telemetry_sample is not None
            and telemetry_sample.vehicle_id != vehicle.vehicle_id
        ):
            raise ValueError(
                "telemetry sample and vehicle belong to different "
                f"vehicles ('{telemetry_sample.vehicle_id}' vs "
                f"'{vehicle.vehicle_id}')"
            )

    @staticmethod
    def _recommendation_sort_key(
        recommendation: MaintenanceRecommendation,
    ) -> tuple[int, float, str, str]:
        return (
            PRIORITY_RANK[recommendation.priority],
            recommendation.remaining_km,
            recommendation.component,
            recommendation.maintenance_type.value,
        )

    @property
    def estimators(self) -> tuple[MaintenanceEstimator, ...]:
        """Estimators registered with this service."""
        return self._estimators

    @property
    def config(self) -> MaintenanceConfig:
        """Configuration used by this service."""
        return self._config
