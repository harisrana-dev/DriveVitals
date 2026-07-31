"""
Engine Health Analyzer.

Evaluates ONLY the engine subsystem.

Health starts at 100 and is reduced gradually by continuous deductions:

    * RPM above the redline
    * Sustained high RPM across the recent window
    * Engine overheating (elevated coolant temperature)
    * Sustained very high engine load
    * Excessive throttle abuse
    * Aggressive throttle events accumulated during the trip

Deductions are proportional to how far the signal exceeds its
threshold, so small fluctuations around normal operation have no
effect on the score.
"""

from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    EngineThresholds,
    StatusThresholds,
    excess_penalty,
    fraction_penalty,
    window_fraction,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class EngineHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the engine subsystem.
    Inputs:
        A telemetry window (newest sample last) and the current
        analytics snapshot.
    Outputs:
        A SubsystemHealth for the engine subsystem.
    """

    def __init__(
        self,
        *,
        thresholds: EngineThresholds | None = None,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        super().__init__(status_thresholds=status_thresholds)
        config = DEFAULT_HEALTH_CONFIG
        self._thresholds = (
            thresholds if thresholds is not None else config.engine
        )

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.ENGINE

    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        current = samples[-1]
        return (
            self._redline_rpm_term(current),
            self._sustained_rpm_term(samples),
            self._overheating_term(current),
            self._sustained_load_term(samples),
            self._throttle_abuse_term(samples),
            self._aggressive_throttle_events_term(snapshot),
        )

    def _redline_rpm_term(
        self,
        sample: TelemetrySample,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        amount = excess_penalty(
            sample.rpm,
            thresholds.redline_rpm,
            thresholds.redline_rpm,
            thresholds.redline_deduction,
        )
        reason = (
            f"rpm above redline ({sample.rpm:.0f} rpm)"
            if amount
            else ""
        )
        return amount, reason

    def _sustained_rpm_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(
            samples,
            lambda sample: sample.rpm >= thresholds.sustained_rpm,
        )
        amount = fraction_penalty(
            fraction,
            thresholds.sustained_rpm_fraction,
            thresholds.sustained_rpm_deduction,
        )
        reason = (
            f"sustained high rpm ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason

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
            f"engine overheating ({sample.coolant_temperature_c:.0f} C)"
            if amount
            else ""
        )
        return amount, reason

    def _sustained_load_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(
            samples,
            lambda sample: sample.engine_load_percent
            >= thresholds.max_load_percent,
        )
        amount = fraction_penalty(
            fraction,
            thresholds.max_load_fraction,
            thresholds.max_load_deduction,
        )
        reason = (
            f"sustained high engine load ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason

    def _throttle_abuse_term(
        self,
        samples: Sequence[TelemetrySample],
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        fraction = window_fraction(
            samples,
            lambda sample: sample.throttle_position_percent
            >= thresholds.throttle_abuse_percent,
        )
        amount = fraction_penalty(
            fraction,
            thresholds.throttle_abuse_fraction,
            thresholds.throttle_abuse_deduction,
        )
        reason = (
            f"excessive throttle abuse ({fraction:.0%} of window)"
            if amount
            else ""
        )
        return amount, reason

    def _aggressive_throttle_events_term(
        self,
        snapshot: AnalyticsSnapshot,
    ) -> tuple[float, str]:
        thresholds = self._thresholds
        count = sum(
            1
            for event in snapshot.completed_events
            if event.event_type == "aggressive_throttle"
        )
        amount = min(count, thresholds.aggressive_throttle_event_cap) * (
            thresholds.aggressive_throttle_event_deduction
        )
        reason = f"aggressive throttle events ({count})" if amount else ""
        return amount, reason
