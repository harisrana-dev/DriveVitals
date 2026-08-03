"""
Subsystem health analyzer interface.

Every subsystem analyzer is responsible for exactly ONE subsystem. The
base class owns the shared scoring flow (deductions -> score -> status)
so individual analyzers only define which deductions apply.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from backend.analytics.snapshot.analytics_snapshot import AnalyticsSnapshot
from backend.analytics.vehicle_health.health_config import (
    DEFAULT_HEALTH_CONFIG,
    StatusThresholds,
    clamp_score,
    status_for_score,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class SubsystemHealthAnalyzer(ABC):
    """
    Purpose:
        Evaluate exactly one subsystem from a telemetry window and the
        current analytics snapshot.
    Inputs:
        samples: recent telemetry window for the vehicle (newest last).
        snapshot: current analytics snapshot (behaviour + events).
    Outputs:
        A SubsystemHealth for the analyzer's subsystem.

    Scoring model:
        Health starts at 100 and each applicable deduction is
        subtracted. Deductions are continuous, so small fluctuations
        below the configured thresholds have no effect.
    """

    def __init__(
        self,
        *,
        status_thresholds: StatusThresholds | None = None,
    ) -> None:
        config = DEFAULT_HEALTH_CONFIG
        self._status_thresholds = (
            status_thresholds
            if status_thresholds is not None
            else config.status
        )

    @property
    @abstractmethod
    def subsystem(self) -> Subsystem:
        """The single subsystem this analyzer evaluates."""

    @abstractmethod
    def _deductions(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> tuple[tuple[float, str], ...]:
        """
        Return the (deduction, reason) contributions that apply.

        A contribution with a zero deduction and an empty reason is
        allowed and is ignored by the base scoring flow.
        """

    def analyze(
        self,
        *,
        samples: Sequence[TelemetrySample],
        snapshot: AnalyticsSnapshot,
    ) -> SubsystemHealth:
        """
        Evaluate the analyzer's subsystem and return its health.
        """
        if not samples:
            raise ValueError("at least one telemetry sample is required")

        contributions = [
            (amount, reason)
            for amount, reason in self._deductions(
                samples=samples,
                snapshot=snapshot,
            )
            if amount > 0.0
        ]

        score = clamp_score(
            100.0 - sum(amount for amount, _ in contributions)
        )
        status = status_for_score(score, self._status_thresholds)

        return SubsystemHealth(
            subsystem=self.subsystem,
            score=score,
            status=status,
            reasons=tuple(reason for _, reason in contributions),
        )


__all__ = ["SubsystemHealthAnalyzer"]
