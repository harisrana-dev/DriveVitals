"""
Analytics Engine.

Central telemetry consumer that combines live runtime state with
immutable analytics context and produces AnalysisInput objects for
future analytics analyzers.
"""

from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.context.context_store import AnalyticsContextStore
from backend.analytics.input.analysis_input import AnalysisInput
from backend.analytics.state.runtime_state_store import RuntimeStateStore
from backend.telemetry.models.telemetry_sample import TelemetrySample


class AnalyticsEngine:
    """Consumes telemetry and prepares structured analytics input."""

    def __init__(
        self,
        runtime_store: RuntimeStateStore,
        context_store: AnalyticsContextStore,
    ) -> None:
        self._runtime_store = runtime_store
        self._context_store = context_store

        self._latest_inputs: dict[str, AnalysisInput] = {}

    def consume(self, sample: TelemetrySample) -> None:
        """
        Consume telemetry and construct the latest AnalysisInput
        for the corresponding vehicle.
        """

        runtime_state = self._runtime_store.update(sample)

        context = self._context_store.get(sample.vehicle_id)

        if context is None:
            raise ValueError(
                f"No analytics context registered for vehicle "
                f"'{sample.vehicle_id}'."
            )

        analysis_input = AnalysisInput(
            runtime_state=runtime_state,
            context=context,
        )

        self._latest_inputs[sample.vehicle_id] = analysis_input

    def get_input(self, vehicle_id: str) -> AnalysisInput | None:
        """Return the latest analysis input for a vehicle."""
        return self._latest_inputs.get(vehicle_id)

    @property
    def runtime_store(self) -> RuntimeStateStore:
        return self._runtime_store

    @property
    def context_store(self) -> AnalyticsContextStore:
        return self._context_store