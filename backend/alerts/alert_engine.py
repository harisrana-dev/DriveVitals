"""
Alert Engine.

Orchestrates alert generators and collects their FleetAlert output.
The engine never decides what constitutes an alert — generators do.

    Recommendations + HealthSnapshot + Telemetry + Trip
                        ↓
                   AlertContext
                        ↓
                  Alert Generators
                        ↓
                    FleetAlerts
"""

from collections.abc import Iterable, Sequence

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.alerts.generators import AlertContext, AlertGenerator
from backend.alerts.models.fleet_alert import FleetAlert
from backend.fleet.models.trip import Trip
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class AlertEngine:
    """
    Purpose:
        Orchestrate alert generators into a single alert output.
    Inputs:
        Maintenance recommendations, health snapshots, telemetry,
        trips, and behaviour events.
    Outputs:
        FleetAlert objects.
    TODO:
        Decide whether alerts should be deduplicated or throttled
        before being returned.
    """

    def __init__(
        self,
        *,
        generators: Sequence[AlertGenerator],
    ) -> None:
        self._generators = tuple(generators)

    def generate_alerts(
        self,
        *,
        recommendations: Iterable[MaintenanceRecommendation] = (),
        health_snapshot: HealthSnapshot | None = None,
        telemetry: Iterable[TelemetrySample] = (),
        trip: Trip | None = None,
        behaviour_events: Iterable[BehaviourEvent] = (),
    ) -> tuple[FleetAlert, ...]:
        """
        Build an AlertContext and delegate to every generator.

        TODO: Implement. Assemble the context, call each generator,
        and return the collected alerts.
        """
        raise NotImplementedError

    @property
    def generators(self) -> tuple[AlertGenerator, ...]:
        """Generators registered with this engine."""
        return self._generators
