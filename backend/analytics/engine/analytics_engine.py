"""
Analytics Engine.

Central telemetry consumer that receives TelemetrySamples from the
pipeline and delegates state updates to the RuntimeStateStore. This
is the entry point for all analytics processing — analyzers, rules,
and scoring will be wired in later milestones.

For now the engine is a thin pass-through: consume → store.
"""

from backend.analytics.state.runtime_state_store import RuntimeStateStore
from backend.telemetry.models.telemetry_sample import TelemetrySample


class AnalyticsEngine:
    """Consumes telemetry and maintains runtime state."""

    def __init__(self, store: RuntimeStateStore) -> None:
        self._store = store

    def consume(self, sample: TelemetrySample) -> None:
        self._store.update(sample)

    @property
    def store(self) -> RuntimeStateStore:
        return self._store
