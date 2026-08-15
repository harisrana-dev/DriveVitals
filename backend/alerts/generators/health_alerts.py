"""
Vehicle Health Alerts Generator.

Generates alerts only for vehicle health signals.
"""

from collections.abc import Callable, Iterable

from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    AlertConfig,
    HealthAlertConfig,
    health_category,
)
from backend.alerts.generators import (
    AlertContext,
    AlertGenerator,
    make_alert,
)
from backend.alerts.models.fleet_alert import (
    AlertSeverity,
    AlertType,
    FleetAlert,
)
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.analytics.vehicle_health.models.subsystem_health import (
    HealthStatus,
    SubsystemHealth,
)


class HealthAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate vehicle health-related alerts.
    Inputs:
        AlertContext (uses health_snapshot).
    Outputs:
        FleetAlert objects of type HEALTH.
    """

    _SUBSYSTEM_ATTRIBUTES: tuple[tuple[str, Callable[[HealthSnapshot], SubsystemHealth]], ...] = (
        ("engine", lambda snapshot: snapshot.engine_health),
        ("cooling", lambda snapshot: snapshot.cooling_health),
        ("transmission", lambda snapshot: snapshot.transmission_health),
        ("brakes", lambda snapshot: snapshot.brake_health),
        ("fuel_system", lambda snapshot: snapshot.fuel_system_health),
    )

    def __init__(
        self,
        *,
        config: AlertConfig | None = None,
    ) -> None:
        """
        Parameters
        ----------
        config:
            Alert configuration. Defaults to DEFAULT_ALERT_CONFIG.
        """
        self._config = config if config is not None else DEFAULT_ALERT_CONFIG

    @property
    def alert_type(self) -> AlertType:
        return AlertType.HEALTH

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate health alerts from context.health_snapshot.

        Alerts fire only for statuses enabled by the configured
        alert_statuses, so a healthy snapshot produces no alerts.
        """
        snapshot = context.health_snapshot
        if snapshot is None:
            return ()

        alerts: list[FleetAlert] = []

        overall = self._alert_for_status(
            snapshot=snapshot,
            slug="overall",
            status=snapshot.overall_status,
            score=snapshot.overall_health_score,
        )
        if overall is not None:
            alerts.append(overall)

        for slug, getter in self._SUBSYSTEM_ATTRIBUTES:
            subsystem_health = getter(snapshot)
            alert = self._alert_for_status(
                snapshot=snapshot,
                slug=slug,
                status=subsystem_health.status,
                score=subsystem_health.score,
            )
            if alert is not None:
                alerts.append(alert)

        return tuple(alerts)

    def _alert_for_status(
        self,
        *,
        snapshot: HealthSnapshot,
        slug: str,
        status: HealthStatus,
        score: float,
    ) -> FleetAlert | None:
        config: HealthAlertConfig = self._config.health
        if status not in config.alert_statuses:
            return None
        severity = config.status_severity.get(status, AlertSeverity.CRITICAL)
        return make_alert(
            alert_id=f"health_{slug}_{status.value}",
            vehicle_id=snapshot.vehicle_id,
            alert_type=self.alert_type,
            severity=severity,
            category=health_category(slug),
            evidence={
                "subsystem": slug,
                "status": status.value,
                "score": score,
                "timestamp": snapshot.timestamp.isoformat(),
            },
            message=(
                f"{slug.replace('_', ' ')} health is {status.value} "
                f"(score {score:.0f}/100)"
            ),
            created_at=snapshot.timestamp,
            driver_id=snapshot.driver_id,
            trip_id=snapshot.trip_id,
        )
