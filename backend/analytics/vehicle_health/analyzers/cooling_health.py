"""
Cooling Health Analyzer.

Evaluates ONLY the cooling subsystem.
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


class CoolingHealthAnalyzer(SubsystemHealthAnalyzer):
    """
    Purpose:
        Assess the health of the cooling subsystem.
    Inputs:
        Telemetry samples, behaviour events, and optional trip context.
    Outputs:
        A SubsystemHealth for the cooling subsystem.
    TODO:
        Define cooling-specific scoring rules and thresholds once the
        architecture is approved.
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
        return Subsystem.COOLING

    def analyze(
        self,
        *,
        samples: Iterable[TelemetrySample],
        behaviour_events: Iterable[BehaviourEvent],
        trip: Trip | None,
    ) -> SubsystemHealth:
        """
        Evaluate cooling health.

        TODO: Implement. Candidate inputs include
        coolant_temperature_c and engine_load_percent.
        """
        raise NotImplementedError
