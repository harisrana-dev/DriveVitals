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
            Merge → Deduplicate → Sort
                        ↓
                    FleetAlerts
"""

from collections.abc import Iterable, Sequence

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    SEVERITY_RANK,
    AlertConfig,
)
from backend.alerts.deduplication import DuplicateSuppressor
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
        FleetAlert objects, deduplicated and ordered by severity.
    """

    def __init__(
        self,
        *,
        generators: Sequence[AlertGenerator],
        config: AlertConfig | None = None,
    ) -> None:
        if not generators:
            raise ValueError("at least one alert generator is required")

        self._config = config if config is not None else DEFAULT_ALERT_CONFIG
        self._generators = tuple(generators)
        self._deduplicator = DuplicateSuppressor(
            cooldown_seconds=self._config.duplicate_cooldown_seconds
        )

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

        The outputs are merged, deduplicated within the cooldown window,
        and returned sorted by severity (critical first) and then by
        timestamp (newest first).
        """
        context = AlertContext(
            recommendations=tuple(recommendations),
            health_snapshot=health_snapshot,
            telemetry=tuple(telemetry),
            trip=trip,
            behaviour_events=tuple(behaviour_events),
        )

        alerts: list[FleetAlert] = []
        for generator in self._generators:
            alerts.extend(generator.generate(context=context))

        deduplicated = self._deduplicator.filter(alerts)
        return tuple(sorted(deduplicated, key=self._sort_key))

    def reset_deduplication(self) -> None:
        """Forget all remembered alert emission times."""
        self._deduplicator.clear()

    @property
    def generators(self) -> tuple[AlertGenerator, ...]:
        """Generators registered with this engine."""
        return self._generators

    @property
    def config(self) -> AlertConfig:
        """Configuration used by this engine."""
        return self._config

    @staticmethod
    def _sort_key(alert: FleetAlert) -> tuple[int, float, str]:
        """Critical first, then newest first, then alert id for stability."""
        return (
            SEVERITY_RANK[alert.severity],
            -alert.created_at.timestamp(),
            alert.alert_id,
        )
