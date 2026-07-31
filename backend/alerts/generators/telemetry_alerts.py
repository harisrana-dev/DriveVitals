"""
Telemetry Alerts Generator.

Generates alerts only for telemetry-related signals.
"""

from collections.abc import Iterable, Mapping

from backend.alerts.generators import AlertContext, AlertGenerator
from backend.alerts.models.fleet_alert import AlertType, FleetAlert


class TelemetryAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate telemetry-related alerts.
    Inputs:
        AlertContext (uses telemetry).
    Outputs:
        FleetAlert objects of type TELEMETRY.
    TODO:
        Define rules for which telemetry patterns become alerts.
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
        return AlertType.TELEMETRY

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate telemetry alerts from context.telemetry.

        TODO: Implement telemetry alert rules.
        """
        raise NotImplementedError
