"""
Duplicate suppression for the Alert subsystem.

Suppresses repeated emissions of the same alert within a configured
cooldown window. Keeps at most one alert per key per batch, keeping the
newest, and then drops any key that was emitted too recently.

The suppressor is stateful on purpose: cooldown requires remembering the
last emission time for every alert key.
"""

from collections.abc import Iterable
from datetime import datetime, timezone

from backend.alerts.models.fleet_alert import FleetAlert


def _as_utc(value: datetime) -> datetime:
    """Normalise a timestamp to an aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class DuplicateSuppressor:
    """
    Purpose:
        Suppress duplicate FleetAlert emissions within a cooldown window.
    Inputs:
        FleetAlert objects produced by the generators.
    Outputs:
        The same alerts with duplicates removed.
    """

    def __init__(self, *, cooldown_seconds: float) -> None:
        if cooldown_seconds < 0.0:
            raise ValueError("cooldown_seconds must be non-negative")
        self._cooldown_seconds = cooldown_seconds
        self._last_emitted: dict[tuple[str, str], datetime] = {}

    def filter(self, alerts: Iterable[FleetAlert]) -> tuple[FleetAlert, ...]:
        """
        Remove duplicates within the batch and within the cooldown window.

        For each alert key the newest member of the batch is kept, then
        it is suppressed if the same key was emitted less than the
        cooldown ago.
        """
        newest: dict[tuple[str, str], FleetAlert] = {}
        for alert in alerts:
            key = self._key(alert)
            current = newest.get(key)
            if (
                current is None
                or _as_utc(alert.created_at)
                > _as_utc(current.created_at)
            ):
                newest[key] = alert

        emitted: list[FleetAlert] = []
        for alert in newest.values():
            key = self._key(alert)
            created_at = _as_utc(alert.created_at)
            last = self._last_emitted.get(key)
            if last is None:
                self._last_emitted[key] = created_at
                emitted.append(alert)
                continue
            elapsed_seconds = (created_at - last).total_seconds()
            if elapsed_seconds >= self._cooldown_seconds:
                self._last_emitted[key] = created_at
                emitted.append(alert)

        return tuple(emitted)

    def clear(self) -> None:
        """Forget every remembered emission time."""
        self._last_emitted.clear()

    @staticmethod
    def _key(alert: FleetAlert) -> tuple[str, str]:
        return (alert.vehicle_id, alert.alert_id)


__all__ = ["DuplicateSuppressor"]
