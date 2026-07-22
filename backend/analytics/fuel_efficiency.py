"""FuelEfficiencyAnalyzer: computes fuel efficiency from real physics data.

Uses PhysicsTickResult.distance_travelled_km and
PhysicsTickResult.fuel_consumed_liters to compute km/liter.
No fabrication — returns unavailable only when genuine data is absent.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class FuelEfficiencyAnalyzer:
    """Computes fuel efficiency from real Digital Twin physics metrics."""

    #: Rating thresholds for km/liter
    EXCELLENT_THRESHOLD: float = 15.0
    GOOD_THRESHOLD: float = 10.0
    AVERAGE_THRESHOLD: float = 5.0

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        events: list[AnalyticsEvent],
    ) -> dict:
        """Compute fuel efficiency from real per-tick physics data.

        Args:
            analytics_input: Current tick's observations including
                physics metrics (distance_travelled_km, fuel_consumed_liters)
                and accumulated trip data.
            events: Rule engine events for this tick.

        Returns:
            Dict with fuel efficiency status and metrics.
        """
        fuel_consumed = analytics_input.fuel_consumed_liters
        distance = analytics_input.distance_travelled_km

        # No physics data available
        if fuel_consumed is None or distance is None:
            return {
                "status": "unavailable",
                "reason": "physics_tick_result_not_available",
                "fuel_level_percent": analytics_input.fuel_level_percent,
            }

        # Zero fuel consumption — idle or electric
        if fuel_consumed <= 0:
            return {
                "status": "ok",
                "mode": "idle",
                "distance_travelled_km": round(distance, 6),
                "fuel_consumed_liters": round(fuel_consumed, 6),
                "km_per_liter": None,
                "rating": "idle",
                "fuel_level_percent": analytics_input.fuel_level_percent,
            }

        # Zero distance but fuel consumed — unusual, report as-is
        if distance <= 0:
            return {
                "status": "ok",
                "mode": "stationary",
                "distance_travelled_km": round(distance, 6),
                "fuel_consumed_liters": round(fuel_consumed, 6),
                "km_per_liter": 0.0,
                "rating": "poor",
                "fuel_level_percent": analytics_input.fuel_level_percent,
            }

        # Normal calculation
        km_per_liter = distance / fuel_consumed

        if km_per_liter >= self.EXCELLENT_THRESHOLD:
            rating = "excellent"
        elif km_per_liter >= self.GOOD_THRESHOLD:
            rating = "good"
        elif km_per_liter >= self.AVERAGE_THRESHOLD:
            rating = "average"
        else:
            rating = "poor"

        return {
            "status": "ok",
            "mode": "driving",
            "distance_travelled_km": round(distance, 6),
            "fuel_consumed_liters": round(fuel_consumed, 6),
            "km_per_liter": round(km_per_liter, 2),
            "rating": rating,
            "fuel_level_percent": analytics_input.fuel_level_percent,
        }
