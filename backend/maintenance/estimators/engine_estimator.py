"""
Engine Maintenance Estimator.

Estimates maintenance needs for the engine subsystem only.

The estimator shortens engine service intervals when the latest
telemetry shows the engine running under stress (overheating or above
the redline), because oil and components degrade faster under those
conditions.
"""

from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.maintenance.estimators.component_estimator import (
    ComponentEstimator,
)
from backend.maintenance.maintenance_config import ServiceProfile
from backend.telemetry.models.telemetry_sample import TelemetrySample


class EngineEstimator(ComponentEstimator):
    """
    Purpose:
        Estimate engine maintenance from a HealthSnapshot.
    Inputs:
        A HealthSnapshot (uses engine_health), current odometer and the
        latest telemetry sample.
    Outputs:
        A list of MaintenanceRecommendation objects for the engine.
    """

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.ENGINE

    @property
    def services(self) -> tuple[ServiceProfile, ...]:
        return self._config.engine_services

    @property
    def component(self) -> str:
        return "engine"

    def condition_factor(
        self,
        telemetry_sample: TelemetrySample | None,
    ) -> float:
        if telemetry_sample is None:
            return 1.0
        thresholds = self._config.engine
        if (
            telemetry_sample.coolant_temperature_c
            >= thresholds.overheat_temp_c
        ):
            return thresholds.stress_factor
        if telemetry_sample.rpm >= thresholds.redline_rpm:
            return thresholds.stress_factor
        return 1.0
