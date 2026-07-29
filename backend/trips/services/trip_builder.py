from datetime import datetime

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.context.analytics_context import (
    AnalyticsContext,
)
from backend.analytics.state.runtime_state import (
    RuntimeAnalyticsState,
)
from backend.trips.schemas.trip_payload import (
    TripSnapshot,
)


def _compute_grade(
    score: float,
) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _compute_safety_score(
    summary: DriverBehaviourSummary,
) -> float:
    score = 100.0
    score -= summary.speeding_event_count * 5
    score -= summary.harsh_braking_count * 4
    score -= summary.aggressive_throttle_event_count * 4
    score -= summary.high_rpm_event_count * 3
    score -= summary.severe_event_count * 8
    score -= summary.moderate_event_count * 4
    return max(0.0, min(100.0, score))


_EVENT_TYPE_LABELS = {
    "speeding": "Speeding",
    "harsh_braking": "Harsh Braking",
    "aggressive_throttle": "Aggressive Throttle",
    "high_rpm": "High RPM",
}


def _build_event_dict(
    event: BehaviourEvent,
) -> dict:
    return {
        "event_type": event.event_type,
        "label": _EVENT_TYPE_LABELS.get(
            event.event_type,
            event.event_type,
        ),
        "started_at": event.started_at.isoformat(),
        "ended_at": event.ended_at.isoformat(),
        "duration_seconds": event.duration_seconds,
        "distance_km": event.distance_km,
        "severity": event.severity,
        "max_speed_excess_kmh": event.max_speed_excess_kmh,
        "max_rpm": event.max_rpm,
        "max_throttle_percent": event.max_throttle_percent,
        "max_braking_intensity": event.max_braking_intensity,
    }


class TripBuilder:
    def build(
        self,
        summary: DriverBehaviourSummary,
        context: AnalyticsContext,
        runtime_state: RuntimeAnalyticsState,
        events: list[BehaviourEvent],
    ) -> TripSnapshot:
        vehicle_name = (
            f"{context.vehicle_year} "
            f"{context.vehicle_make} "
            f"{context.vehicle_model}"
        )

        safety_score = _compute_safety_score(summary)

        average_speed_kmh = 0.0
        duration_seconds = 0.0
        maximum_speed_kmh = 0.0
        fuel_consumed_liters = 0.0
        average_fuel_rate_lph = 0.0

        if summary.total_distance_km > 0:
            average_speed_kmh = runtime_state.speed_kmh
            maximum_speed_kmh = runtime_state.speed_kmh
            duration_seconds = runtime_state.odometer_km / max(average_speed_kmh, 1.0) * 3600 if average_speed_kmh > 0 else 0.0
            fuel_consumed_liters = runtime_state.fuel_rate_lph * (duration_seconds / 3600) if average_speed_kmh > 0 else 0.0
            average_fuel_rate_lph = runtime_state.fuel_rate_lph

        event_dicts = tuple(
            _build_event_dict(evt)
            for evt in events
        )

        return TripSnapshot(
            trip_id=summary.trip_id,
            vehicle_id=summary.vehicle_id,
            driver_id=summary.driver_id,
            vehicle_name=vehicle_name,
            driver_name=context.driver_name or None,
            route_id=context.route_id,
            route_type=context.route_type,
            distance_km=summary.total_distance_km,
            duration_seconds=duration_seconds,
            average_speed_kmh=average_speed_kmh,
            maximum_speed_kmh=maximum_speed_kmh,
            fuel_consumed_liters=fuel_consumed_liters,
            average_fuel_rate_lph=average_fuel_rate_lph,
            safety_score=safety_score,
            overall_grade=_compute_grade(safety_score),
            started_at=None,
            completed_at=runtime_state.timestamp,
            speeding_event_count=summary.speeding_event_count,
            speeding_duration_seconds=summary.speeding_duration_seconds,
            harsh_braking_count=summary.harsh_braking_count,
            aggressive_throttle_event_count=summary.aggressive_throttle_event_count,
            aggressive_throttle_duration_seconds=summary.aggressive_throttle_duration_seconds,
            high_rpm_event_count=summary.high_rpm_event_count,
            high_rpm_duration_seconds=summary.high_rpm_duration_seconds,
            severe_event_count=summary.severe_event_count,
            moderate_event_count=summary.moderate_event_count,
            minor_event_count=summary.minor_event_count,
            overall_severity=summary.overall_severity,
            events=event_dicts,
        )
