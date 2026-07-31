"""
Vehicle Health Alerts Generator.

Generates alerts only for vehicle health signals.
"""

from collections.abc import Iterable, Mapping

from backend.alerts.generators import AlertContext, AlertGenerator
from backend.alerts.models.fleet_alert import AlertType, FleetAlert


class HealthAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate vehicle health-related alerts.
    Inputs:
        AlertContext (uses health_snapshot).
    Outputs:
        FleetAlert objects of type HEALTH.
    TODO:
        Define rules for which health signals become alerts.
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
            Future generator-specific thresholds. Intentionally left
            undefined in this milestone so no values are guessed.
        """
        self._thresholds = thresholds

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

        TODO: Implement health alert rules.
        """
        raise NotImplementedError
