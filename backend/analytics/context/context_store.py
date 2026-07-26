"""
Analytics Context Store.

Maintains immutable contextual information required by the analytics
engine to interpret telemetry.
"""

from backend.analytics.context.analytics_context import AnalyticsContext


class AnalyticsContextStore:
    """In-memory store of analytics context keyed by vehicle ID."""

    def __init__(self) -> None:
        self._contexts: dict[str, AnalyticsContext] = {}

    def register(self, context: AnalyticsContext) -> None:
        """Register or replace the context for a vehicle."""
        self._contexts[context.vehicle_id] = context

    def get(self, vehicle_id: str) -> AnalyticsContext | None:
        """Return the context for a vehicle, if registered."""
        return self._contexts.get(vehicle_id)

    def remove(self, vehicle_id: str) -> None:
        """Remove a vehicle's context."""
        self._contexts.pop(vehicle_id, None)

    def clear(self) -> None:
        """Remove all registered contexts."""
        self._contexts.clear()

    def all_contexts(self) -> list[AnalyticsContext]:
        """Return all registered contexts."""
        return list(self._contexts.values())

    def __len__(self) -> int:
        """Return the number of registered contexts."""
        return len(self._contexts)