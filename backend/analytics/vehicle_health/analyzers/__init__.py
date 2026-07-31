"""
Subsystem health analyzer interface.

Every subsystem analyzer is responsible for exactly ONE subsystem.
Keeping the interface in this package lets the VehicleHealthEngine
orchestrate analyzers without knowing subsystem-specific details.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)
from backend.fleet.models.trip import Trip
from backend.telemetry.models.telemetry_sample import TelemetrySample


class SubsystemHealthAnalyzer(ABC):
    """
    Purpose:
        Interface implemented by every subsystem health analyzer.
    Inputs:
        Telemetry samples, behaviour events, and optional trip context.
    Outputs:
        A SubsystemHealth for the analyzer's single subsystem.
    TODO:
        Decide whether analyzer-specific thresholds should be passed to
        the constructor or resolved from a shared configuration.
    """

    @property
    @abstractmethod
    def subsystem(self) -> Subsystem:
        """The single subsystem this analyzer evaluates."""
        raise NotImplementedError

    @abstractmethod
    def analyze(
        self,
        *,
        samples: Iterable[TelemetrySample],
        behaviour_events: Iterable[BehaviourEvent],
        trip: Trip | None,
    ) -> SubsystemHealth:
        """Evaluate the analyzer's subsystem and return its health."""
        raise NotImplementedError


__all__ = ["SubsystemHealthAnalyzer"]
