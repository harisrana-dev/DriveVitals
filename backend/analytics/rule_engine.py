"""RuleEngine: deterministic engineering rule checks against AnalyticsInput.

Produces typed AnalyticsEvent results. Rules only use signals that
actually exist in the current Digital Twin telemetry. Missing signals
cause the rule to be skipped (not a crash, not a fake value).
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class RuleEngine:
    """Evaluates AnalyticsInput against centralized engineering thresholds."""

    # --- Thresholds (class-level constants) ---

    MAX_SPEED_KMH: float = 120.0
    MAX_RPM: float = 5000.0
    MAX_ENGINE_LOAD_PERCENT: float = 85.0
    MAX_ENGINE_TEMPERATURE_C: float = 105.0
    MIN_FUEL_LEVEL_PERCENT: float = 15.0
    MIN_BATTERY_VOLTAGE: float = 11.5
    MAX_IDLE_RPM: float = 1000.0
    IDLE_SPEED_THRESHOLD_KMH: float = 1.0

    def evaluate(self, analytics_input: AnalyticsInput) -> list[AnalyticsEvent]:
        """Run all rules and return triggered events.

        Args:
            analytics_input: Normalized tick observations.

        Returns:
            List of AnalyticsEvent for rules that fired. May be empty.
        """
        events: list[AnalyticsEvent] = []
        events.extend(self._check_overspeed(analytics_input))
        events.extend(self._check_high_rpm(analytics_input))
        events.extend(self._check_high_engine_load(analytics_input))
        events.extend(self._check_high_engine_temperature(analytics_input))
        events.extend(self._check_low_fuel(analytics_input))
        events.extend(self._check_low_battery(analytics_input))
        events.extend(self._check_excessive_idle(analytics_input))
        return events

    # ---------------------------------------------------------------

    def _make_event(
        self,
        rule_id: str,
        event: str,
        category: str,
        severity: str,
        value: float,
        threshold: float,
        analytics_input: AnalyticsInput,
    ) -> AnalyticsEvent:
        return AnalyticsEvent(
            rule_id=rule_id,
            event=event,
            category=category,
            severity=severity,
            vehicle_id=analytics_input.vehicle_id,
            timestamp=analytics_input.timestamp,
            value=value,
            threshold=threshold,
        )

    # ---------------------------------------------------------------

    def _check_overspeed(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.speed_kmh is None or ai.speed_kmh <= self.MAX_SPEED_KMH:
            return []
        return [
            self._make_event(
                "DV-R001", "overspeed", "driver_behaviour", "WARNING",
                ai.speed_kmh, self.MAX_SPEED_KMH, ai,
            )
        ]

    def _check_high_rpm(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.rpm is None or ai.rpm <= self.MAX_RPM:
            return []
        return [
            self._make_event(
                "DV-R002", "high_rpm", "vehicle_health", "WARNING",
                ai.rpm, self.MAX_RPM, ai,
            )
        ]

    def _check_high_engine_load(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.engine_load_percent is None or ai.engine_load_percent <= self.MAX_ENGINE_LOAD_PERCENT:
            return []
        return [
            self._make_event(
                "DV-R003", "high_engine_load", "vehicle_health", "WARNING",
                ai.engine_load_percent, self.MAX_ENGINE_LOAD_PERCENT, ai,
            )
        ]

    def _check_high_engine_temperature(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.engine_temperature_celsius is None or ai.engine_temperature_celsius <= self.MAX_ENGINE_TEMPERATURE_C:
            return []
        return [
            self._make_event(
                "DV-R004", "high_engine_temperature", "vehicle_health", "CRITICAL",
                ai.engine_temperature_celsius, self.MAX_ENGINE_TEMPERATURE_C, ai,
            )
        ]

    def _check_low_fuel(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.fuel_level_percent is None or ai.fuel_level_percent >= self.MIN_FUEL_LEVEL_PERCENT:
            return []
        return [
            self._make_event(
                "DV-R005", "low_fuel", "fuel_efficiency", "WARNING",
                ai.fuel_level_percent, self.MIN_FUEL_LEVEL_PERCENT, ai,
            )
        ]

    def _check_low_battery(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.battery_voltage is None or ai.battery_voltage >= self.MIN_BATTERY_VOLTAGE:
            return []
        return [
            self._make_event(
                "DV-R006", "low_battery", "vehicle_health", "WARNING",
                ai.battery_voltage, self.MIN_BATTERY_VOLTAGE, ai,
            )
        ]

    def _check_excessive_idle(self, ai: AnalyticsInput) -> list[AnalyticsEvent]:
        if ai.speed_kmh is None or ai.rpm is None:
            return []
        if ai.speed_kmh >= self.IDLE_SPEED_THRESHOLD_KMH or ai.rpm <= self.MAX_IDLE_RPM:
            return []
        return [
            self._make_event(
                "DV-R007", "excessive_idle", "driver_behaviour", "INFO",
                ai.rpm, self.MAX_IDLE_RPM, ai,
            )
        ]
