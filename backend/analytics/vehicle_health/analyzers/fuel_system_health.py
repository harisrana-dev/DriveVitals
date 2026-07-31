"""
Fuel System Health Analyzer.

Evaluates ONLY the fuel system subsystem.

Health starts at 100 and is reduced gradually by continuous deductions:

    * Poor fuel efficiency under normal engine load across the window
    * Excessive fuel consumption at normal load across the window
    * High throttle combined with a high fuel rate on the current sample

Efficiency is only evaluated on samples inside the normal operating
band, so high fuel consumption justified by high load is not penalised.
"""

from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    FuelSystemThresholds,
    StatusThresholds,
    excess_penalty,
    fraction_penalty,
    mean,
    window_fraction,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class FuelSystemHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the fuel system subsystem.
    Inputs:
        A telemetry window (newest sample last) and the current
        analytics snapshot.
    Outputs:
        A SubsystemHealth for the fuel system subsystem.
    """

    def __init__(
        self,
        *,
        thresholds: FuelSystemThresholds | None = None,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        super().__init__(status_thresholds=status_thresholds)
        config = DEFAULT_HEALTH_CONFIG
        self._thresholds = (
            thresholds if thresholds is not None else config.fuel_system
        )

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.FUEL_SYSTEM

    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        current = samples[-1]
        return (
            self._poor_efficiency_term(samples),
            self._excessive_consumption_term(samples),
            self._high_throttle_consumption_term(current),
        )

    def _efficiency_samples(
        self,
        samples: Sequence[TelemetrySample],
    ) -> list[float]:
        thresholds = self._thresholds
        efficiencies = []
        for sample in samples:
            if (
                sample.speed_kmh >= thresholds.min_speed_kmh
                and sample.fuel_rate_lph > 0.1
                and thresholds.normal_load_min_percent
                <= sample.engine_load_percent
                <= thresholds.normal_load_max_percent
            ):
                efficiencies.append(sample.speed_kmh / sample.fuel_rate_lph)
        return efficiencies

    def _poor_efficiency_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        average = mean(self._efficiency_samples(samples))
        if average <= 0.0:
            return 0.0, ""
        amount = excess_penalty(
            thresholds.min_efficiency_km_per_l,
            average,
            thresholds.min_efficiency_km_per_l,
            thresholds.efficiency_deduction,
        )
        reason = (
            f"poor fuel efficiency ({average:.1f} km/L under normal load)"
            if amount
            else ""
        )
        return amount, reason

    def _excessive_consumption_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(
            samples,
            lambda sample: sample.fuel_rate_lph
            > thresholds.high_fuel_rate_lph
            and sample.engine_load_percent
            <= thresholds.normal_load_max_percent,
        )
        amount = fraction_penalty(
            fraction,
            thresholds.high_consumption_fraction,
            thresholds.high_consumption_deduction,
        )
        reason = (
            f"excessive fuel consumption ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason

    def _high_throttle_consumption_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        amount = 0.0
        if (
            sample.throttle_position_percent
            >= thresholds.abuse_throttle_percent
            and sample.fuel_rate_lph > thresholds.high_fuel_rate_lph
        ):
            amount = thresholds.abuse_deduction
        reason = (
            f"high throttle fuel use (throttle {sample.throttle_position_percent:.0f}%)"
            if amount
            else ""
        )
        return amount, reason
