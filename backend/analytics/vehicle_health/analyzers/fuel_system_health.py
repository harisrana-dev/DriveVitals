"""
Fuel System Health Analyzer.

Evaluates ONLY the fuel system subsystem.
"""

from collections.abc import Iterable, Mapping

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)
from backend.fleet.models.trip import Trip
from backend.telemetry.models.telemetry_sample import TelemetrySample


class FuelSystemHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the fuel system subsystem.
    Inputs:
        Telemetry samples, behaviour events, and optional trip context.
    Outputs:
        A SubsystemHealth for the fuel system subsystem.
    TODO:
        Define fuel-system-specific scoring rules and thresholds once
        the architecture is approved.
    """

    def __init__(
        self,
        *,
        thresholds: Mapping[str, float] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        thresholds:
            Future analyzer-specific thresholds. Intentionally left
            undefined in this milestone so no values are guessed.
        """
        self._thresholds = thresholds

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.FUEL_SYSTEM

    def analyze(
        self,
        *,
        samples: Iterable[TelemetrySample],
        behaviour_events: Iterable[BehaviourEvent],
        trip: Trip | None,
    ) -> SubsystemHealth:
        """
        Evaluate fuel system health.

        TODO: Implement. Candidate inputs include fuel_rate_lph,
        fuel_level_percent, and throttle_position_percent.
        """
        raise NotImplementedError
