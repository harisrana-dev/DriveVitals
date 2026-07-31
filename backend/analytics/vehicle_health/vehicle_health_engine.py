"""
Vehicle Health Engine.

Coordinates the subsystem health analyzers and produces a
HealthSnapshot. The engine owns orchestration only — every scoring
decision belongs to a dedicated analyzer.

    Telemetry + Behaviour + Trip
                ↓
          Subsystem Analyzers
                ↓
          HealthSnapshot
"""

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.analyzers import (
    SubsystemHealthAnalyzer,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    Subsystem,
    SubsystemHealth,
)
from backend.fleet.models.trip import Trip
from backend.telemetry.models.telemetry_sample import TelemetrySample


class VehicleHealthEngine:
    """
    Purpose:
        Orchestrate subsystem analyzers into a single HealthSnapshot.
    Inputs:
        Telemetry samples, behaviour events, and optional trip context.
    Outputs:
        A HealthSnapshot for one vehicle.
    TODO:
        Decide whether the engine should expose raw subsystem results
        separately (e.g. for observability) alongside the snapshot.
    """

    def __init__(
        self,
        *,
        analyzers: Sequence[SubsystemHealthAnalyzer],
    ) -> None:
        self._analyzers = tuple(analyzers)

    def analyze(
        self,
        *,
        samples: Iterable[TelemetrySample],
        behaviour_events: Iterable[BehaviourEvent],
        trip: Trip | None,
    ) -> HealthSnapshot:
        """
        Run every subsystem analyzer and combine the results.

        TODO: Implement. Delegates to each analyzer and assembles a
        HealthSnapshot via generate_snapshot.
        """
        raise NotImplementedError

    def generate_snapshot(
        self,
        *,
        vehicle_id: str,
        timestamp: datetime,
        subsystem_healths: Mapping[Subsystem, SubsystemHealth],
    ) -> HealthSnapshot:
        """
        Assemble a HealthSnapshot from per-subsystem results.

        TODO: Implement. Must derive the overall_health_score from the
        subsystem scores without mutating them.
        """
        raise NotImplementedError

    @property
    def analyzers(self) -> tuple[SubsystemHealthAnalyzer, ...]:
        """Analyzers registered with this engine."""
        return self._analyzers
