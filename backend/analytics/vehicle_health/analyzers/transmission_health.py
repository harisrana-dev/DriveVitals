"""
Transmission Health Analyzer.

Evaluates ONLY the transmission subsystem.

Health starts at 100 and is reduced gradually by continuous deductions:

    * Poor operating conditions on the current sample: high RPM at low
      speed combined with heavy throttle (drivetrain lugging)
    * Repeated drivetrain stress across the recent window

A stress sample requires all three conditions to hold at once so normal
slow driving is never mistaken for transmission abuse.
"""

from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    StatusThresholds,
    TransmissionThresholds,
    excess_penalty,
    fraction_penalty,
    window_fraction,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class TransmissionHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the transmission subsystem.
    Inputs:
        A telemetry window (newest sample last) and the current
        analytics snapshot.
    Outputs:
        A SubsystemHealth for the transmission subsystem.
    """

    def __init__(
        self,
        *,
        thresholds: TransmissionThresholds | None = None,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        super().__init__(status_thresholds=status_thresholds)
        config = DEFAULT_HEALTH_CONFIG
        self._thresholds = (
            thresholds if thresholds is not None else config.transmission
        )

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.TRANSMISSION

    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        current = samples[-1]
        return (
            self._poor_condition_term(current),
            self._repeated_stress_term(samples),
        )

    def _is_stress_sample(self, sample: TelemetrySample) -> bool:
        thresholds = self._thresholds
        return (
            sample.speed_kmh < thresholds.low_speed_kmh
            and sample.rpm > thresholds.stress_rpm
            and sample.throttle_position_percent
            > thresholds.stress_throttle_percent
        )

    def _poor_condition_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        amount = 0.0
        if self._is_stress_sample(sample):
            amount = excess_penalty(
                sample.rpm,
                thresholds.stress_rpm,
                thresholds.stress_rpm,
                thresholds.stress_deduction,
            )
        reason = (
            f"high rpm at low speed ({sample.rpm:.0f} rpm at {sample.speed_kmh:.0f} km/h)"
            if amount
            else ""
        )
        return amount, reason

    def _repeated_stress_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(samples, self._is_stress_sample)
        amount = fraction_penalty(
            fraction,
            thresholds.stress_fraction,
            thresholds.stress_fraction_deduction,
        )
        reason = (
            f"repeated drivetrain stress ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason
