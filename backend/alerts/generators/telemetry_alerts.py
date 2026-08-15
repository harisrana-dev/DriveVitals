"""
Telemetry Alerts Generator.

Generates alerts only for telemetry-related signals.
"""

from collections.abc import Iterable

from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    TELEMETRY_COOLANT_CRITICAL,
    TELEMETRY_ENGINE_OVERHEATING,
    TELEMETRY_FUEL_CRITICAL,
    TELEMETRY_RPM_REDLINE,
    AlertConfig,
    TelemetryAlertConfig,
    category_for,
)
from backend.alerts.generators import (
    AlertContext,
    AlertGenerator,
    make_alert,
)
from backend.alerts.models.fleet_alert import (
    AlertType,
    FleetAlert,
)
from backend.telemetry.models.telemetry_sample import TelemetrySample


class TelemetryAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate telemetry-related alerts.
    Inputs:
        AlertContext (uses telemetry).
    Outputs:
        FleetAlert objects of type TELEMETRY.
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
        return AlertType.TELEMETRY

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate telemetry alerts from context.telemetry.

        Each sample is checked against the configured thresholds; a
        sample can trigger more than one condition.
        """
        config: TelemetryAlertConfig = self._config.telemetry

        alerts: list[FleetAlert] = []
        for sample in context.telemetry:
            alerts.extend(self._alerts_for_sample(sample, config))
        return tuple(alerts)

    def _alerts_for_sample(
        self,
        sample: TelemetrySample,
        config: TelemetryAlertConfig,
    ) -> Iterable[FleetAlert]:
        alerts: list[FleetAlert] = []

        if sample.coolant_temperature_c >= config.engine_overheat_temp_c:
            alerts.append(
                make_alert(
                    alert_id=TELEMETRY_ENGINE_OVERHEATING,
                    vehicle_id=sample.vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.engine_overheat_severity,
                    category=category_for(
                        TELEMETRY_ENGINE_OVERHEATING, self.alert_type
                    ),
                    evidence={
                        "signal": "coolant_temperature_c",
                        "value": sample.coolant_temperature_c,
                        "unit": "C",
                        "threshold": config.engine_overheat_temp_c,
                        "timestamp": sample.timestamp.isoformat(),
                    },
                    message=(
                        "Engine overheating: coolant "
                        f"{sample.coolant_temperature_c:.1f} C exceeds "
                        f"{config.engine_overheat_temp_c:.1f} C"
                    ),
                    created_at=sample.timestamp,
                    driver_id=sample.driver_id,
                    trip_id=sample.trip_id,
                )
            )

        if sample.coolant_temperature_c >= config.coolant_critical_temp_c:
            alerts.append(
                make_alert(
                    alert_id=TELEMETRY_COOLANT_CRITICAL,
                    vehicle_id=sample.vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.coolant_critical_severity,
                    category=category_for(
                        TELEMETRY_COOLANT_CRITICAL, self.alert_type
                    ),
                    evidence={
                        "signal": "coolant_temperature_c",
                        "value": sample.coolant_temperature_c,
                        "unit": "C",
                        "threshold": config.coolant_critical_temp_c,
                        "timestamp": sample.timestamp.isoformat(),
                    },
                    message=(
                        "Coolant critical: temperature "
                        f"{sample.coolant_temperature_c:.1f} C exceeds "
                        f"{config.coolant_critical_temp_c:.1f} C"
                    ),
                    created_at=sample.timestamp,
                    driver_id=sample.driver_id,
                    trip_id=sample.trip_id,
                )
            )

        if sample.fuel_level_percent <= config.fuel_critical_percent:
            alerts.append(
                make_alert(
                    alert_id=TELEMETRY_FUEL_CRITICAL,
                    vehicle_id=sample.vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.fuel_critical_severity,
                    category=category_for(
                        TELEMETRY_FUEL_CRITICAL, self.alert_type
                    ),
                    evidence={
                        "signal": "fuel_level_percent",
                        "value": sample.fuel_level_percent,
                        "unit": "%",
                        "threshold": config.fuel_critical_percent,
                        "timestamp": sample.timestamp.isoformat(),
                    },
                    message=(
                        "Fuel critically low: "
                        f"{sample.fuel_level_percent:.1f}% is at or below "
                        f"{config.fuel_critical_percent:.1f}%"
                    ),
                    created_at=sample.timestamp,
                    driver_id=sample.driver_id,
                    trip_id=sample.trip_id,
                )
            )

        if sample.rpm >= config.redline_rpm:
            alerts.append(
                make_alert(
                    alert_id=TELEMETRY_RPM_REDLINE,
                    vehicle_id=sample.vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.redline_severity,
                    category=category_for(
                        TELEMETRY_RPM_REDLINE, self.alert_type
                    ),
                    evidence={
                        "signal": "rpm",
                        "value": sample.rpm,
                        "unit": "rpm",
                        "threshold": config.redline_rpm,
                        "timestamp": sample.timestamp.isoformat(),
                    },
                    message=(
                        f"RPM at redline: {sample.rpm:.0f} exceeds "
                        f"{config.redline_rpm:.0f}"
                    ),
                    created_at=sample.timestamp,
                    driver_id=sample.driver_id,
                    trip_id=sample.trip_id,
                )
            )

        return tuple(alerts)
