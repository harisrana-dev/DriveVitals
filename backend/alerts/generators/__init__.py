"""
Alert generator interface.

Each generator is responsible for one alert category. The Alert Engine
orchestrates generators; generators never inspect each other and never
decide what another category should emit.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.alerts.models.fleet_alert import AlertType, FleetAlert
from backend.fleet.models.trip import Trip
from backend.maintenance.models.maintenance_recommendation import (
    MaintenanceRecommendation,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


@dataclass(frozen=True, slots=True)
class AlertContext:
    """
    Purpose:
        Bundle all inputs the Alert Engine hands to generators.
    Inputs:
        Assembled by the Alert Engine.
    Outputs:
        Consumed by every alert generator.
    TODO:
        Decide whether the context should carry trip-level summaries
        instead of raw behaviour events.
    """

    recommendations: tuple[MaintenanceRecommendation, ...] = ()
    health_snapshot: HealthSnapshot | None = None
    telemetry: tuple[TelemetrySample, ...] = ()
    trip: Trip | None = None
    behaviour_events: tuple[BehaviourEvent, ...] = ()


class AlertGenerator(ABC):
    """
    Purpose:
        Interface implemented by every alert generator.
    Inputs:
        An AlertContext.
    Outputs:
        FleetAlert objects for the generator's category.
    """

    @property
    @abstractmethod
    def alert_type(self) -> AlertType:
        """The alert category this generator produces."""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """Generate alerts from the supplied context."""
        raise NotImplementedError


__all__ = [
    "AlertGenerator",
    "AlertContext",
]
