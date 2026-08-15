"""
Alert generator interface.

Each generator is responsible for one alert category. The Alert Engine
orchestrates generators; generators never inspect each other and never
decide what another category should emit.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.analytics.vehicle_health.models.health_snapshot import (
    HealthSnapshot,
)
from backend.alerts.models.fleet_alert import (
    AlertCategory,
    AlertSeverity,
    AlertType,
    FleetAlert,
)
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
    """

    recommendations: tuple[MaintenanceRecommendation, ...] = ()
    health_snapshot: HealthSnapshot | None = None
    telemetry: tuple[TelemetrySample, ...] = ()
    trip: Trip | None = None
    behaviour_events: tuple[BehaviourEvent, ...] = ()


def make_alert(
    *,
    alert_id: str,
    vehicle_id: str,
    alert_type: AlertType,
    severity: AlertSeverity,
    message: str,
    created_at: datetime,
    driver_id: str | None = None,
    trip_id: str | None = None,
    condition: str | None = None,
    category: AlertCategory = AlertCategory.OTHER,
    evidence: dict | None = None,
    source: str = "alert_engine",
) -> FleetAlert:
    """Assemble one FleetAlert from the generator's findings.

    ``condition`` defaults to the canonical ``alert_id`` so callers only
    pass it when the condition key differs from the emitted id.
    """
    return FleetAlert(
        alert_id=alert_id,
        vehicle_id=vehicle_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        created_at=created_at,
        driver_id=driver_id,
        trip_id=trip_id,
        condition=condition if condition is not None else alert_id,
        category=category,
        evidence=evidence,
        source=source,
    )


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


from backend.alerts.generators.health_alerts import HealthAlertsGenerator
from backend.alerts.generators.maintenance_alerts import (
    MaintenanceAlertsGenerator,
)
from backend.alerts.generators.telemetry_alerts import TelemetryAlertsGenerator
from backend.alerts.generators.trip_alerts import TripAlertsGenerator

__all__ = [
    "AlertGenerator",
    "AlertContext",
    "make_alert",
    "HealthAlertsGenerator",
    "MaintenanceAlertsGenerator",
    "TelemetryAlertsGenerator",
    "TripAlertsGenerator",
]
