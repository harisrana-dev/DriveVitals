"""
Active-trip snapshot builder.

Builds a unified :class:`TripSnapshot` for a trip that is still in
progress, using only authoritative live state:

    * ``trip``            -> identity, route, started_at, live distance
    * ``context``         -> vehicle/driver/route display metadata
    * ``runtime_state``   -> live telemetry (current speed, fuel, ...)
    * ``behaviour``       -> live point-in-time behaviour flags
    * ``summary``         -> behaviour events accumulated so far this trip
    * ``events``          -> the completed behaviour events for the trip

The completed-trip ``TripBuilder`` remains the single owner of final
metrics. This builder never fabricates completion values: completion-only
fields (``safety_score``, ``grade``, ``completed_at``) stay ``None`` and
numerical fields that cannot be computed yet stay ``0.0``/``False``, which
the frontend renders honestly as "not available".
"""

from datetime import datetime

from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
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
from backend.fleet.models.trip import (
    Trip,
)
from backend.trips.schemas.trip_payload import (
    TripSnapshot,
)
from backend.trips.services.trip_builder import (
    _build_event_dict,
)


def _duration_seconds(
    started_at: datetime | None,
    now: datetime,
) -> float:
    if started_at is None:
        return 0.0
    return max(0.0, (now - started_at).total_seconds())


def _average_speed_kmh(
    distance_km: float,
    duration_seconds: float,
) -> float:
    if duration_seconds <= 0:
        return 0.0
    return round(
        distance_km / (duration_seconds / 3600),
        2,
    )


def build_active_trip_snapshot(
    *,
    trip: Trip,
    context: AnalyticsContext,
    runtime_state: RuntimeAnalyticsState | None = None,
    behaviour: DriverBehaviourAnalysis | None = None,
    active_event_types: tuple[str, ...] = (),
    summary: DriverBehaviourSummary | None = None,
    events: list[BehaviourEvent] | None = None,
    fuel_consumed_liters: float | None = None,
    now: datetime,
) -> TripSnapshot:
    """
    Build a unified TripSnapshot for an in-progress trip.

    ``now`` is the runtime tick time and drives the live duration.
    All completion-only fields remain unset.
    """

    vehicle_name = (
        f"{context.vehicle_year} "
        f"{context.vehicle_make} "
        f"{context.vehicle_model}"
    )

    duration_seconds = _duration_seconds(
        trip.started_at,
        now,
    )

    distance_km = max(0.0, trip.distance_travelled_km)

    average_speed_kmh = _average_speed_kmh(
        distance_km,
        duration_seconds,
    )

    maximum_speed_kmh = 0.0
    if (
        summary is not None
        and summary.maximum_speed_excess_kmh > 0.0
    ):
        maximum_speed_kmh = round(
            context.speed_limit_kmh
            + summary.maximum_speed_excess_kmh,
            2,
        )

    average_fuel_rate_lph = 0.0
    if (
        fuel_consumed_liters is not None
        and fuel_consumed_liters > 0.0
        and duration_seconds > 0
    ):
        average_fuel_rate_lph = round(
            fuel_consumed_liters / (duration_seconds / 3600),
            2,
        )

    event_list = list(events or [])

    return TripSnapshot(
        trip_id=trip.trip_id,
        vehicle_id=trip.vehicle_id,
        driver_id=trip.driver_id,
        vehicle_name=vehicle_name,
        driver_name=context.driver_name or None,
        route_id=trip.route_id,
        route_type=context.route_type,
        route_name=context.route_name or None,
        status="in_progress",
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        average_speed_kmh=average_speed_kmh,
        maximum_speed_kmh=maximum_speed_kmh,
        fuel_consumed_liters=(
            fuel_consumed_liters
            if fuel_consumed_liters is not None
            else 0.0
        ),
        average_fuel_rate_lph=average_fuel_rate_lph,
        safety_score=None,
        grade=None,
        started_at=trip.started_at,
        completed_at=None,
        speeding_event_count=(
            summary.speeding_event_count
            if summary is not None
            else 0
        ),
        speeding_duration_seconds=(
            summary.speeding_duration_seconds
            if summary is not None
            else 0.0
        ),
        harsh_braking_count=(
            summary.harsh_braking_count
            if summary is not None
            else 0
        ),
        aggressive_throttle_event_count=(
            summary.aggressive_throttle_event_count
            if summary is not None
            else 0
        ),
        aggressive_throttle_duration_seconds=(
            summary.aggressive_throttle_duration_seconds
            if summary is not None
            else 0.0
        ),
        high_rpm_event_count=(
            summary.high_rpm_event_count
            if summary is not None
            else 0
        ),
        high_rpm_duration_seconds=(
            summary.high_rpm_duration_seconds
            if summary is not None
            else 0.0
        ),
        severe_event_count=(
            summary.severe_event_count
            if summary is not None
            else 0
        ),
        moderate_event_count=(
            summary.moderate_event_count
            if summary is not None
            else 0
        ),
        minor_event_count=(
            summary.minor_event_count
            if summary is not None
            else 0
        ),
        overall_severity=(
            summary.overall_severity
            if summary is not None
            else "normal"
        ),
        events=tuple(
            _build_event_dict(evt)
            for evt in event_list
        ),
        current_speed_kmh=(
            runtime_state.speed_kmh
            if runtime_state is not None
            else None
        ),
        speeding=(
            behaviour.speeding
            if behaviour is not None
            else False
        ),
        harsh_braking=(
            behaviour.harsh_braking
            if behaviour is not None
            else False
        ),
        aggressive_throttle=(
            behaviour.aggressive_throttle
            if behaviour is not None
            else False
        ),
        high_rpm=(
            behaviour.high_rpm
            if behaviour is not None
            else False
        ),
    )
