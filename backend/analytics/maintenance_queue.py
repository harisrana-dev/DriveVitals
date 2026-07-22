"""MaintenanceQueueAnalyzer: rule-based maintenance recommendations.

Generates maintenance items based on actual available telemetry
signals and analytics results. No fabrication of recommendations
from unavailable data.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class MaintenanceQueueAnalyzer:
    """Produces maintenance recommendations from available signals."""

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        analytics_results: dict,
    ) -> list[dict]:
        """Generate maintenance recommendations.

        Args:
            analytics_input: Current tick's normalized observations.
            analytics_results: Full analytics results dict for this tick
                (includes vehicle_health, rule events, etc.).

        Returns:
            List of maintenance recommendation dicts.
        """
        maintenance: list[dict] = []
        health = analytics_results.get("vehicle_health", {})
        vehicle_id = analytics_input.vehicle_id

        # Engine temperature
        temp = analytics_input.engine_temperature_celsius
        if temp is not None and temp >= 100:
            maintenance.append({
                "vehicle_id": vehicle_id,
                "priority": "High",
                "maintenance": "Cooling System Inspection",
                "remaining": "Immediate",
            })

        # Engine load + RPM combination
        load = analytics_input.engine_load_percent
        rpm = analytics_input.rpm
        if load is not None and rpm is not None:
            if load >= 85 and rpm > 3500:
                maintenance.append({
                    "vehicle_id": vehicle_id,
                    "priority": "Medium",
                    "maintenance": "Engine Inspection",
                    "remaining": "500 km",
                })

        # Vehicle health critical
        if health.get("health") == "critical":
            maintenance.append({
                "vehicle_id": vehicle_id,
                "priority": "High",
                "maintenance": "Immediate Workshop Visit",
                "remaining": "Immediate",
            })

        # Brake pad health
        brake = analytics_input.brake_pad_health_percent
        if brake is not None and brake < 30:
            maintenance.append({
                "vehicle_id": vehicle_id,
                "priority": "High",
                "maintenance": "Brake Service",
                "remaining": "Immediate",
            })

        # Tyre health
        tyre = analytics_input.tyre_health_percent
        if tyre is not None and tyre < 30:
            maintenance.append({
                "vehicle_id": vehicle_id,
                "priority": "Medium",
                "maintenance": "Tyre Replacement",
                "remaining": "500 km",
            })

        # Battery voltage
        battery = analytics_input.battery_voltage
        if battery is not None and battery < 11.5:
            maintenance.append({
                "vehicle_id": vehicle_id,
                "priority": "Medium",
                "maintenance": "Battery Service",
                "remaining": "700 km",
            })

        return maintenance
