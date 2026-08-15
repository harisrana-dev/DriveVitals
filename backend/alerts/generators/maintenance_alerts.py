"""
Maintenance Alerts Generator.

Generates alerts only for maintenance-related signals.
"""

import re
from collections.abc import Iterable
from datetime import datetime, timezone

from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    AlertConfig,
    MaintenanceAlertConfig,
)
from backend.alerts.generators import (
    AlertContext,
    AlertGenerator,
    make_alert,
)
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)

from backend.alerts.models.fleet_alert import (
    AlertCategory,
    AlertSeverity,
    AlertType,
    FleetAlert,
)


def _slugify(value: str) -> str:
    """Lowercase a component name into an alert id slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def maintenance_alert_id(component: str, maintenance_type) -> str:
    """Canonical alert key for one maintenance recommendation.

    Shared by the generator (which emits alerts) and the runtime (which
    computes the currently-active set for stale resolution).
    """
    return (
        "maintenance_"
        f"{_slugify(component)}_"
        f"{maintenance_type.value}"
    )


class MaintenanceAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate maintenance-related alerts.
    Inputs:
        AlertContext (uses recommendations).
    Outputs:
        FleetAlert objects of type MAINTENANCE.
    """

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
        return AlertType.MAINTENANCE

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate maintenance alerts from context.recommendations.

        Each recommendation becomes one alert whose severity mirrors the
        recommendation priority. No maintenance estimation is repeated.
        """
        config: MaintenanceAlertConfig = self._config.maintenance
        now = datetime.now(timezone.utc)

        alerts: list[FleetAlert] = []
        for recommendation in context.recommendations:
            severity = config.priority_severity.get(
                recommendation.priority,
                AlertSeverity.LOW,
            )
            alerts.append(
                make_alert(
                    alert_id=maintenance_alert_id(
                        recommendation.component,
                        recommendation.maintenance_type,
                    ),
                    vehicle_id=recommendation.vehicle_id,
                    alert_type=self.alert_type,
                    severity=severity,
                    category=AlertCategory.MAINTENANCE,
                    evidence={
                        "component": recommendation.component,
                        "maintenance_type": recommendation.maintenance_type.value,
                        "priority": recommendation.priority.value,
                        "remaining_km": recommendation.remaining_km,
                        "recommended_action": recommendation.recommended_action,
                        "reason": recommendation.reason,
                    },
                    message=(
                        f"{recommendation.recommended_action}: "
                        f"{recommendation.reason}"
                    ),
                    created_at=now,
                )
            )
        return tuple(alerts)
