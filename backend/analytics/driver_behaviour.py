"""DriverBehaviourAnalyzer: rule-based driver behaviour classification.

Evaluates rule engine events and telemetry signals to classify
driver behaviour as normal, aggressive, or idle. Extensible
for future ML model integration.
"""

from __future__ import annotations

from analytics.analytics_events import AnalyticsEvent
from analytics.analytics_input import AnalyticsInput


class DriverBehaviourAnalyzer:
    """Classifies driver behaviour from rule events and telemetry."""

    def analyze(
        self,
        analytics_input: AnalyticsInput,
        events: list[AnalyticsEvent],
    ) -> dict:
        """Analyze driver behaviour based on available signals.

        Args:
            analytics_input: Current tick's normalized observations.
            events: Rule engine events for this tick.

        Returns:
            Dict with status, behaviour classification, and indicators.
        """
        indicators: list[str] = []
        event_keys = {e.event for e in events}

        if "overspeed" in event_keys:
            indicators.append("overspeed_detected")

        if "excessive_idle" in event_keys:
            indicators.append("excessive_idle")

        if "high_rpm" in event_keys and "high_engine_load" in event_keys:
            indicators.append("aggressive_driving_pattern")

        # Classify behaviour
        if not indicators:
            behaviour = "normal"
        elif "aggressive_driving_pattern" in indicators:
            behaviour = "aggressive"
        elif indicators == ["excessive_idle"]:
            behaviour = "idle"
        else:
            behaviour = "normal"

        return {
            "status": "ok",
            "behaviour": behaviour,
            "indicators": indicators,
        }
