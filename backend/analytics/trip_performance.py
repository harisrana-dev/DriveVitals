"""TripPerformanceAnalyzer: trip-level analytics from real Digital Twin data.

Uses trip identity and progress fields from the Trip domain entity,
supplied via AnalyticsInput. Produces meaningful results when an
active trip exists; returns not_initialized when no trip context
is available.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class TripPerformanceAnalyzer:
    """Evaluates trip performance from real trip domain data."""

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        events: list[AnalyticsEvent],
    ) -> dict:
        """Analyze trip performance from real Digital Twin trip data.

        Args:
            analytics_input: Current tick's observations including
                trip identity and progress from the Trip domain entity.
            events: Rule engine events for this tick.

        Returns:
            Dict with trip performance metrics, or not_initialized
            if no trip context is available.
        """
        trip_id = analytics_input.trip_id

        if trip_id is None:
            return {
                "status": "not_initialized",
                "reason": "no_active_trip",
            }

        planned = analytics_input.distance_planned_km or 0.0
        completed = analytics_input.distance_completed_km or 0.0
        duration = analytics_input.duration_minutes or 0.0
        avg_speed = analytics_input.average_speed_kmh or 0.0
        fuel_consumed = analytics_input.fuel_consumed_liters or 0.0
        fuel_efficiency = analytics_input.fuel_efficiency_km_per_liter or 0.0

        # Calculate progress percentage
        if planned > 0:
            progress_percent = round((completed / planned) * 100, 2)
        else:
            progress_percent = 0.0

        distance_remaining = max(0.0, planned - completed)

        return {
            "status": "in_progress",
            "trip_id": trip_id,
            "driver_id": analytics_input.driver_id,
            "distance_planned_km": round(planned, 4),
            "distance_completed_km": round(completed, 4),
            "progress_percent": progress_percent,
            "distance_remaining_km": round(distance_remaining, 4),
            "duration_minutes": round(duration, 4),
            "average_speed_kmh": round(avg_speed, 2),
            "fuel_consumed_liters": round(fuel_consumed, 6),
            "fuel_efficiency_km_per_liter": round(fuel_efficiency, 2),
        }
