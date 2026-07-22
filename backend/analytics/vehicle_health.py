"""VehicleHealthAnalyzer: deterministic health scoring from AnalyticsInput.

Evaluates available vehicle-health signals and produces a structured
health report with a deterministic, explainable score.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class VehicleHealthAnalyzer:
    """Scores vehicle health from available telemetry signals."""

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        events: list[AnalyticsEvent],
    ) -> dict:
        """Evaluate vehicle health and return a structured report.

        Args:
            analytics_input: Current tick's normalized observations.
            events: Rule engine events for this tick.

        Returns:
            Dict with keys: status, health_score, health, factors.
        """
        score = 100.0
        factors: list[str] = []

        # Engine temperature
        temp = analytics_input.engine_temperature_celsius
        if temp is not None:
            if temp > 105:
                score -= 25
                factors.append(f"engine_temperature_critical_{temp:.1f}c")
            elif temp > 95:
                score -= 10
                factors.append(f"engine_temperature_high_{temp:.1f}c")

        # Engine load
        load = analytics_input.engine_load_percent
        if load is not None and load > 80:
            score -= 5
            factors.append(f"engine_load_high_{load:.1f}%")

        # RPM
        rpm = analytics_input.rpm
        if rpm is not None and rpm > 4500:
            score -= 5
            factors.append(f"rpm_high_{rpm:.0f}")

        # Battery voltage
        battery = analytics_input.battery_voltage
        if battery is not None and battery < 12.0:
            score -= 10
            factors.append(f"battery_low_{battery:.2f}V")

        # Brake pad health
        brake = analytics_input.brake_pad_health_percent
        if brake is not None and brake < 50:
            score -= 15
            factors.append(f"brake_pad_low_{brake:.1f}%")

        # Tyre health
        tyre = analytics_input.tyre_health_percent
        if tyre is not None and tyre < 50:
            score -= 15
            factors.append(f"tyre_low_{tyre:.1f}%")

        # Clamp score
        score = max(0.0, min(100.0, score))

        # Determine health status
        if score >= 80:
            health = "healthy"
        elif score >= 50:
            health = "warning"
        else:
            health = "critical"

        return {
            "status": "ok",
            "health_score": round(score, 1),
            "health": health,
            "factors": factors,
        }
