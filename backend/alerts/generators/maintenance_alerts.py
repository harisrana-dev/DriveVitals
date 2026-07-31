"""
Maintenance Alerts Generator.

Generates alerts only for maintenance-related signals.
"""

from collections.abc import Iterable, Mapping

from backend.alerts.generators import AlertContext, AlertGenerator
from backend.alerts.models.fleet_alert import AlertType, FleetAlert


class MaintenanceAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate maintenance-related alerts.
    Inputs:
        AlertContext (uses recommendations).
    Outputs:
        FleetAlert objects of type MAINTENANCE.
    TODO:
        Define rules for which recommendations become alerts.
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
        return AlertType.MAINTENANCE

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate maintenance alerts from context.recommendations.

        TODO: Implement maintenance alert rules.
        """
        raise NotImplementedError
