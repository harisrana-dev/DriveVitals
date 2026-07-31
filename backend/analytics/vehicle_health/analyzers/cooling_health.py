"""
Cooling Health Analyzer.

Evaluates ONLY the cooling subsystem.

Health starts at 100 and is reduced gradually by continuous deductions:

    * Overheating (coolant temperature beyond the overheat threshold)
    * Elevated coolant temperature below the overheat threshold
    * Unstable coolant temperature across the recent window
    * High sustained thermal load (mean engine load)

A stable operating temperature maintains health: a low window
standard deviation produces no deduction.
"""

from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    CoolingThresholds,
    StatusThresholds,
    excess_penalty,
    mean,
    standard_deviation,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class CoolingHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the cooling subsystem.
    Inputs:
        A telemetry window (newest sample last) and the current
        analytics snapshot.
    Outputs:
        A SubsystemHealth for the cooling subsystem.
    """

    def __init__(
        self,
        *,
        thresholds: CoolingThresholds | None = None,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        super().__init__(status_thresholds=status_thresholds)
        config = DEFAULT_HEALTH_CONFIG
        self._thresholds = (
            thresholds if thresholds is not None else config.cooling
        )

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.COOLING

    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        current = samples[-1]
        temperatures = [
            sample.coolant_temperature_c for sample in samples
        ]
        loads = [sample.engine_load_percent for sample in samples]
        return (
            self._overheating_term(current),
            self._elevated_temperature_term(current),
            self._temperature_stability_term(temperatures),
            self._thermal_load_term(loads),
        )

    def _overheating_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        amount = excess_penalty(
            sample.coolant_temperature_c,
            thresholds.overheat_temp_c,
            thresholds.overheat_span_c,
            thresholds.overheat_deduction,
        )
        reason = (
            f"overheating ({sample.coolant_temperature_c:.0f} C)"
            if amount
            else ""
        )
        return amount, reason

    def _elevated_temperature_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        amount = excess_penalty(
            sample.coolant_temperature_c,
            thresholds.elevated_temp_c,
            thresholds.elevated_span_c,
            thresholds.elevated_deduction,
        )
        reason = (
            f"elevated coolant temperature ({sample.coolant_temperature_c:.0f} C)"
            if amount
            else ""
        )
        return amount, reason

    def _temperature_stability_term(
        self,
        temperatures: Sequence[float],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        deviation = standard_deviation(temperatures)
        amount = excess_penalty(
            deviation,
            thresholds.stability_stddev_c,
            thresholds.stability_span_c,
            thresholds.stability_deduction,
        )
        reason = (
            f"unstable coolant temperature (stddev {deviation:.1f} C)"
            if amount
            else ""
        )
        return amount, reason

    def _thermal_load_term(
        self,
        loads: Sequence[float],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        span = 100.0 - thresholds.max_load_percent
        average = mean(loads)
        amount = excess_penalty(
            average,
            thresholds.max_load_percent,
            span,
            thresholds.max_load_deduction,
        )
        reason = (
            f"high thermal load (mean {average:.0f}%)"
            if amount
            else ""
        )
        return amount, reason
