from dataclasses import dataclass
from datetime import datetime

from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.telemetry.models.telemetry_sample import (
    TelemetrySample,
)


@dataclass(frozen=True, slots=True)
class AnalyticsSnapshot:
    """
    Immutable point-in-time analytics state for one vehicle.

    Represents the combined result of:

        TelemetrySample
              +
        DriverBehaviourAnalysis
              +
        Completed BehaviourEvents
              +
        Currently Active Events
    """

    vehicle_id: str
    driver_id: str
    trip_id: str
    timestamp: datetime

    telemetry: TelemetrySample

    behaviour: DriverBehaviourAnalysis

    completed_events: tuple[
        BehaviourEvent,
        ...

    ]

    active_event_types: tuple[str, ...]