"""
Shared component estimator base.

Every subsystem estimator follows the same deterministic flow, so the
flow lives here once:

    subsystem health score
        -> severity + remaining-life factor
        -> remaining distance per service profile
        -> priority + recommendation
        -> MaintenanceRecommendation

A concrete estimator only declares which subsystem it owns and which
service profiles apply to it, and may tighten the remaining distance
based on current operating conditions.
"""

from abc import abstractmethod

from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)
from backend.maintenance.estimation.rules import (
    estimated_due_date,
    health_factor,
    interval_remaining_km,
    priority_for,
    severity_for,
)
from backend.maintenance.maintenance_config import (
    DEFAULT_MAINTENANCE_CONFIG,
    MaintenanceConfig,
    ServiceProfile,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
    MaintenanceSeverity,
)
from backend.maintenance.estimators.maintenance_estimator import (
    MaintenanceEstimator,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample

_SUBSYSTEM_HEALTH_ATTRIBUTE: dict[Subsystem, str] = {
    Subsystem.ENGINE: "engine_health",
    Subsystem.COOLING: "cooling_health",
    Subsystem.TRANSMISSION: "transmission_health",
    Subsystem.BRAKES: "brake_health",
    Subsystem.FUEL_SYSTEM: "fuel_system_health",
}


class ComponentEstimator(MaintenanceEstimator):
    """
    Purpose:
        Deterministic maintenance estimation for one subsystem.
    Inputs:
        A HealthSnapshot, current odometer and latest telemetry.
    Outputs:
        A list of MaintenanceRecommendation objects.
    """

    def __init__(
        self,
        *,
        config: MaintenanceConfig | None = None,
    ) -> None:
        self._config = (
            config if config is not None else DEFAULT_MAINTENANCE_CONFIG
        )
        self._validate_config(self._config)

    @staticmethod
    def _validate_config(config: MaintenanceConfig) -> None:
        priority = config.priority
        if not (
            priority.low_min_km
            > priority.medium_min_km
            > priority.high_min_km
            > 0.0
        ):
            raise ValueError(
                "priority thresholds must satisfy "
                "low_min > medium_min > high_min > 0"
            )
        severity = config.severity
        if not (
            severity.minor_min_score
            > severity.moderate_min_score
            > 0.0
        ):
            raise ValueError(
                "severity thresholds must satisfy "
                "minor_min > moderate_min > 0"
            )
        if config.daily_distance_km <= 0.0:
            raise ValueError("daily_distance_km must be positive")
        if not 0.0 < config.engine.stress_factor <= 1.0:
            raise ValueError("engine stress_factor must be in (0, 1]")

    @property
    @abstractmethod
    def subsystem(self) -> Subsystem:
        """The subsystem this estimator owns."""
        raise NotImplementedError

    @property
    @abstractmethod
    def services(self) -> tuple[ServiceProfile, ...]:
        """Service profiles this estimator can recommend."""
        raise NotImplementedError

    @property
    def config(self) -> MaintenanceConfig:
        """Configuration used by this estimator."""
        return self._config

    def condition_factor(
        self,
        telemetry_sample: TelemetrySample | None,
    ) -> float:
        """
        Tighten the remaining distance based on current operating
        conditions. Subsystems may override; the default is neutral.
        """
        return 1.0

    def estimate(
        self,
        *,
        health_snapshot: HealthSnapshot,
        odometer_km: float,
        telemetry_sample: TelemetrySample | None = None,
    ) -> list[MaintenanceRecommendation]:
        subsystem_health = self._subsystem_health(health_snapshot)
        score = subsystem_health.score
        severity = severity_for(score, self._config.severity)
        factor = health_factor(score) * self.condition_factor(
            telemetry_sample
        )

        recommendations: list[MaintenanceRecommendation] = []
        for service in self.services:
            remaining_km = (
                interval_remaining_km(odometer_km, service.interval_km)
                * factor
            )
            if not self._should_emit(
                remaining_km=remaining_km,
                score=score,
            ):
                continue
            recommendations.append(
                self._build_recommendation(
                    health_snapshot=health_snapshot,
                    subsystem_health=subsystem_health,
                    service=service,
                    remaining_km=remaining_km,
                    severity=severity,
                )
            )
        return recommendations

    def _should_emit(self, *, remaining_km: float, score: float) -> bool:
        """
        Emit a service when it falls inside the planning horizon (the
        LOW priority band) or when the subsystem is not fully healthy,
        in which case its full service plan is surfaced.
        """
        if score < self._config.severity.minor_min_score:
            return True
        return remaining_km <= self._config.priority.low_min_km

    def _subsystem_health(
        self,
        health_snapshot: HealthSnapshot,
    ) -> SubsystemHealth:
        attribute = _SUBSYSTEM_HEALTH_ATTRIBUTE[self.subsystem]
        return getattr(health_snapshot, attribute)

    def _build_recommendation(
        self,
        *,
        health_snapshot: HealthSnapshot,
        subsystem_health: SubsystemHealth,
        service: ServiceProfile,
        remaining_km: float,
        severity: MaintenanceSeverity,
    ) -> MaintenanceRecommendation:
        priority = priority_for(remaining_km, self._config.priority)
        due_date = estimated_due_date(
            timestamp=health_snapshot.timestamp,
            remaining_km=remaining_km,
            daily_distance_km=self._config.daily_distance_km,
        )
        return MaintenanceRecommendation(
            vehicle_id=health_snapshot.vehicle_id,
            component=self.component,
            maintenance_type=service.maintenance_type,
            priority=priority,
            severity=severity,
            remaining_km=remaining_km,
            reason=self._reason_text(subsystem_health, service, remaining_km),
            recommended_action=service.recommended_action,
            estimated_cost=service.estimated_cost,
            estimated_due_date=due_date,
        )

    def _reason_text(
        self,
        subsystem_health: SubsystemHealth,
        service: ServiceProfile,
        remaining_km: float,
    ) -> str:
        reason = (
            f"{self.component} health {subsystem_health.score:.0f}/100"
        )
        if subsystem_health.reasons:
            reason += (
                f" - {', '.join(subsystem_health.reasons)}"
            )
        reason += (
            f"; {service.label} due in {remaining_km:.0f} km "
            f"(interval {service.interval_km:.0f} km)"
        )
        return reason


__all__ = ["ComponentEstimator"]
