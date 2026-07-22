"""AnalyticsEvent: typed, immutable event produced by the rule engine.

Replaces the loose dictionaries returned by V1 rule checks.
Provides a to_dict() method for backward compatibility with
dashboard code that expects plain dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    """A single deterministic rule violation or observation.

    Attributes:
        rule_id: Stable rule identifier (e.g. "DV-R001").
        event: Short event key (e.g. "overspeed").
        category: Analytics domain (e.g. "driver_behaviour").
        severity: "INFO", "WARNING", or "CRITICAL".
        vehicle_id: Vehicle that triggered the event.
        timestamp: Simulation time of the event.
        value: Observed value that triggered the rule.
        threshold: Threshold that was exceeded or breached.
    """

    rule_id: str
    event: str
    category: str
    severity: str
    vehicle_id: str
    timestamp: datetime
    value: float
    threshold: float

    def to_dict(self) -> dict:
        """Serialize to a plain dict for dashboard / state_manager compat."""
        return {
            "rule_id": self.rule_id,
            "event": self.event,
            "category": self.category,
            "severity": self.severity,
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp,
            "value": self.value,
            "threshold": self.threshold,
        }
