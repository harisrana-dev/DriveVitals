from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.events.event import (
    BehaviourEvent,
)
from backend.analytics.context.analytics_context import (
    AnalyticsContext,
)
from backend.analytics.driver_statistics.safety import (
    compute_grade,
    compute_safety_score_for_summary,
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
    """Build canonical :class:`TripSnapshot` instances for completed trips.

    This is the single owner of final trip metrics. It sources distance,
    duration, and fuel from the completed ``Trip`` object and behaviour
    data from the ``DriverBehaviourSummary``. Active-trip snapshots are
    built by :func:`build_active_trip_snapshot` instead, which never
    fabricates completion values.
    """

    def build(
        self,
        summary: DriverBehaviourSummary,
        context: AnalyticsContext,
        runtime_state: RuntimeAnalyticsState,
        events: list[BehaviourEvent],
        trip: Trip | None = None,
    ) -> TripSnapshot:
        vehicle_name = (
            f"{context.vehicle_year} "
            f"{context.vehicle_make} "
            f"{context.vehicle_model}"
        )

        # --------------------------------------------------------------
        # Trip totals.
        #
        # The completed Trip object is the authoritative source for
        # distance and duration. Never fall back to the lifetime
        # odometer held in runtime_state/summary for distance.
        # --------------------------------------------------------------

        distance_km = (
            trip.distance_travelled_km
            if trip is not None
            else summary.total_distance_km
        )

        duration_seconds = 0.0
        if (
            trip is not None
            and trip.started_at is not None
            and trip.completed_at is not None
        ):
            duration_seconds = (
                trip.completed_at - trip.started_at
            ).total_seconds()

        average_speed_kmh = 0.0
        if duration_seconds > 0:
            average_speed_kmh = round(
                distance_km / (duration_seconds / 3600),
                2,
            )

        maximum_speed_kmh = (
            context.speed_limit_kmh
            + summary.maximum_speed_excess_kmh
        )

        fuel_consumed_liters = (
            trip.fuel_used_liters
            if trip is not None
            else 0.0
        )

        average_fuel_rate_lph = 0.0
        if duration_seconds > 0:
            average_fuel_rate_lph = round(
                fuel_consumed_liters / (duration_seconds / 3600),
                2,
            )

        safety_score = compute_safety_score_for_summary(
            summary,
            distance_km=distance_km,
        )

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
            route_name=context.route_name or None,
            distance_km=distance_km,
            duration_seconds=duration_seconds,
            average_speed_kmh=average_speed_kmh,
            maximum_speed_kmh=maximum_speed_kmh,
            fuel_consumed_liters=fuel_consumed_liters,
            average_fuel_rate_lph=average_fuel_rate_lph,
            safety_score=safety_score,
            grade=compute_grade(safety_score),
            started_at=(
                trip.started_at
                if trip is not None
                else None
            ),
            completed_at=(
                trip.completed_at
                if trip is not None
                else runtime_state.timestamp
            ),
            status=(
                trip.status.value
                if trip is not None
                else "completed"
            ),
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
