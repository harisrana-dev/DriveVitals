"""DriverRankingAnalyzer: cumulative safety scoring per vehicle.

The current Digital Twin telemetry only identifies vehicles, not
drivers. Ranking is vehicle-scoped until driver identity is
explicitly supplied from the domain model. Violations are tracked
per vehicle so the same violation does not repeatedly deduct
penalties every tick.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class DriverRankingAnalyzer:
    """Maintains cumulative safety scores per vehicle."""

    #: Penalty points per violation type (first occurrence only).
    PENALTIES: dict[str, int] = {
        "overspeed": 15,
        "high_rpm": 8,
        "high_engine_load": 5,
        "excessive_idle": 2,
    }

    def __init__(self) -> None:
        #: Track which violation types have been seen per vehicle.
        #: Key: (vehicle_id, event_type), Value: True
        self._active_violations: dict[tuple[str, str], bool] = {}

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        events: list[AnalyticsEvent],
        current_score: int,
    ) -> dict:
        """Update the cumulative safety score for this vehicle.

        Only the first occurrence of each violation type per vehicle
        deducts points. Subsequent ticks with the same violation type
        do not re-deduct.

        Args:
            analytics_input: Current tick's normalized observations.
            events: Rule engine events for this tick.
            current_score: The vehicle's current score (0-100).

        Returns:
            Dict with vehicle_id, score, and grade.
        """
        score = current_score

        for event in events:
            key = (analytics_input.vehicle_id, event.event)
            if key not in self._active_violations:
                score -= self.PENALTIES.get(event.event, 0)
                self._active_violations[key] = True

        score = max(0, score)

        if score >= 90:
            grade = "Excellent"
        elif score >= 80:
            grade = "Good"
        elif score >= 70:
            grade = "Average"
        else:
            grade = "Needs Coaching"

        return {
            "vehicle_id": analytics_input.vehicle_id,
            "score": score,
            "grade": grade,
        }
