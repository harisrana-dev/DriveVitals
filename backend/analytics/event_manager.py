"""EventManager: in-memory event lifecycle manager.

Tracks analytics events across ticks, managing their lifecycle from
ACTIVE through RESOLVED. Identified by (vehicle_id, event_type).

When a rule fires, the event becomes ACTIVE (or increments if already
active). When the rule stops firing, the event transitions to RESOLVED.
Resolved events are retained in a bounded history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TrackedEvent:
    """A live event with lifecycle state.

    Attributes:
        event_type: Short event key (e.g. "overspeed").
        rule_id: Stable rule identifier (e.g. "DV-R001").
        category: Analytics domain (e.g. "driver_behaviour").
        severity: "INFO", "WARNING", or "CRITICAL".
        vehicle_id: Vehicle that triggered the event.
        status: "ACTIVE" or "RESOLVED".
        first_seen_tick: Tick when the event was first detected.
        last_seen_tick: Most recent tick where the event was active.
        first_seen_time: Simulation time of first detection.
        last_seen_time: Simulation time of most recent detection.
        occurrences: Number of consecutive ticks the event was active.
        latest_value: Most recent observed value.
        threshold: Threshold that was exceeded or breached.
    """

    event_type: str
    rule_id: str
    category: str
    severity: str
    vehicle_id: str
    status: str = "ACTIVE"
    first_seen_tick: int = 0
    last_seen_tick: int = 0
    first_seen_time: datetime | None = None
    last_seen_time: datetime | None = None
    occurrences: int = 1
    latest_value: float = 0.0
    threshold: float = 0.0

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "vehicle_id": self.vehicle_id,
            "status": self.status,
            "first_seen_tick": self.first_seen_tick,
            "last_seen_tick": self.last_seen_tick,
            "first_seen_time": self.first_seen_time,
            "last_seen_time": self.last_seen_time,
            "occurrences": self.occurrences,
            "latest_value": self.latest_value,
            "threshold": self.threshold,
        }


class EventManager:
    """Tracks event lifecycle across ticks.

    Identified by (vehicle_id, event_type). Creates on first detection,
    increments while active, resolves when the condition disappears.
    Retains resolved events in a bounded history.
    """

    def __init__(self, max_resolved: int = 200) -> None:
        #: Active events keyed by (vehicle_id, event_type)
        self._active: dict[tuple[str, str], TrackedEvent] = {}
        #: Resolved event history (newest first)
        self._resolved: list[TrackedEvent] = []
        self._max_resolved = max_resolved

    def update(
        self,
        active_event_types: set[tuple[str, str]],
        event_snapshots: dict[tuple[str, str], dict],
        current_tick: int,
    ) -> None:
        """Update event lifecycle for one tick.

        Args:
            active_event_types: Set of (vehicle_id, event_type) tuples
                for events that are currently firing this tick.
            event_snapshots: Map of (vehicle_id, event_type) -> snapshot
                dict with rule_id, category, severity, value, threshold,
                timestamp for events that fired this tick.
            current_tick: Current simulation tick id.
        """
        # 1. Mark newly active or increment existing
        for key in active_event_types:
            snapshot = event_snapshots[key]
            if key in self._active:
                evt = self._active[key]
                evt.occurrences += 1
                evt.last_seen_tick = current_tick
                evt.last_seen_time = snapshot["timestamp"]
                evt.latest_value = snapshot["value"]
            else:
                self._active[key] = TrackedEvent(
                    event_type=key[1],
                    rule_id=snapshot["rule_id"],
                    category=snapshot["category"],
                    severity=snapshot["severity"],
                    vehicle_id=key[0],
                    status="ACTIVE",
                    first_seen_tick=current_tick,
                    last_seen_tick=current_tick,
                    first_seen_time=snapshot["timestamp"],
                    last_seen_time=snapshot["timestamp"],
                    occurrences=1,
                    latest_value=snapshot["value"],
                    threshold=snapshot["threshold"],
                )

        # 2. Resolve events that are no longer active
        to_resolve = [key for key in self._active if key not in active_event_types]
        for key in to_resolve:
            evt = self._active.pop(key)
            evt.status = "RESOLVED"
            self._resolved.insert(0, evt)
            if len(self._resolved) > self._max_resolved:
                self._resolved.pop()

    def get_active_events(self) -> list[TrackedEvent]:
        """Return all currently active events."""
        return list(self._active.values())

    def get_resolved_events(self) -> list[TrackedEvent]:
        """Return resolved event history (newest first)."""
        return list(self._resolved)

    def get_all_events(self) -> list[TrackedEvent]:
        """Return active + resolved events."""
        return self.get_active_events() + self.get_resolved_events()
