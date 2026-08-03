"""Alert engine package."""

from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    AlertConfig,
    HealthAlertConfig,
    MaintenanceAlertConfig,
    TelemetryAlertConfig,
    TripAlertConfig,
)
from backend.alerts.alert_engine import AlertEngine
from backend.alerts.deduplication import DuplicateSuppressor
from backend.alerts.generators import (
    AlertContext,
    AlertGenerator,
    HealthAlertsGenerator,
    MaintenanceAlertsGenerator,
    TelemetryAlertsGenerator,
    TripAlertsGenerator,
)
from backend.alerts.models.fleet_alert import (
    AlertSeverity,
    AlertType,
    FleetAlert,
)

__all__ = [
    "AlertEngine",
    "AlertContext",
    "AlertGenerator",
    "AlertConfig",
    "DEFAULT_ALERT_CONFIG",
    "HealthAlertConfig",
    "MaintenanceAlertConfig",
    "TelemetryAlertConfig",
    "TripAlertConfig",
    "DuplicateSuppressor",
    "HealthAlertsGenerator",
    "MaintenanceAlertsGenerator",
    "TelemetryAlertsGenerator",
    "TripAlertsGenerator",
    "FleetAlert",
    "AlertType",
    "AlertSeverity",
]
