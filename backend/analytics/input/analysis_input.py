"""
Analysis Input.

Immutable bundle of all information required by analytics analyzers
to interpret a telemetry event.
"""

from dataclasses import dataclass

from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.state.runtime_state import RuntimeAnalyticsState


@dataclass(frozen=True)
class AnalysisInput:
    """
    Complete input provided to analytics analyzers.

    RuntimeAnalyticsState:
        Latest observed telemetry snapshot.

    AnalyticsContext:
        Immutable contextual information describing the conditions
        under which the telemetry was generated.
    """

    runtime_state: RuntimeAnalyticsState
    context: AnalyticsContext