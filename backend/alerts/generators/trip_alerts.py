"""
Trip Alerts Generator.

Generates alerts only for trip-related signals.
"""

from collections.abc import Iterable, Mapping

from backend.alerts.generators import AlertContext, AlertGenerator
from backend.alerts.models.fleet_alert import AlertType, FleetAlert


class TripAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate trip-related alerts.
    Inputs:
        AlertContext (uses trip and behaviour_events).
    Outputs:
        FleetAlert objects of type TRIP.
    TODO:
        Define rules for which trip signals become alerts.
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
        return AlertType.TRIP

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate trip alerts from context.trip and
        context.behaviour_events.

        TODO: Implement trip alert rules.
        """
        raise NotImplementedError
