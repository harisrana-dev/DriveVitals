"""
Brake Health Analyzer.

Evaluates ONLY the brake subsystem.

Health starts at 100 and is reduced gradually by continuous deductions:

    * Harsh braking events accumulated during the trip
    * Very high brake pressure on the current sample
    * Sustained frequency of hard braking across the recent window

Deductions are proportional to how far the signal exceeds its
threshold, so occasional braking has no effect on the score.
"""

from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    BrakeThresholds,
    StatusThresholds,
    excess_penalty,
    fraction_penalty,
    window_fraction,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class BrakeHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the brake subsystem.
    Inputs:
        A telemetry window (newest sample last) and the current
        analytics snapshot.
    Outputs:
        A SubsystemHealth for the brake subsystem.
    """

    def __init__(
        self,
        *,
        thresholds: BrakeThresholds | None = None,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        super().__init__(status_thresholds=status_thresholds)
        config = DEFAULT_HEALTH_CONFIG
        self._thresholds = (
            thresholds if thresholds is not None else config.brake
        )

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.BRAKES

    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        current = samples[-1]
        return (
            self._harsh_brake_events_term(snapshot),
            self._brake_pressure_term(current),
            self._hard_brake_frequency_term(samples),
        )

    def _harsh_brake_events_term(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        count = sum(
            1
            for event in snapshot.completed_events
            if event.event_type == "harsh_braking"
        )
        amount = min(count, thresholds.harsh_brake_event_cap) * (
            thresholds.harsh_brake_event_deduction
        )
        reason = f"harsh braking events ({count})" if amount else ""
        return amount, reason

    def _brake_pressure_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        span = 1.0 - thresholds.harsh_brake_pressure
        amount = excess_penalty(
            sample.brake_pressure,
            thresholds.harsh_brake_pressure,
            span,
            thresholds.harsh_pressure_deduction,
        )
        reason = (
            f"harsh braking pressure ({sample.brake_pressure:.2f})"
            if amount
            else ""
        )
        return amount, reason

    def _hard_brake_frequency_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(
            samples,
            lambda sample: sample.brake_pressure
            >= thresholds.hard_brake_pressure,
        )
        amount = fraction_penalty(
            fraction,
            thresholds.hard_brake_fraction,
            thresholds.hard_brake_deduction,
        )
        reason = (
            f"frequent hard braking ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason
