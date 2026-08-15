"""
Trip Alerts Generator.

Generates alerts only for trip-related signals.
"""

from collections.abc import Iterable
from datetime import datetime, timezone

from backend.alerts.alerts_config import (
    DEFAULT_ALERT_CONFIG,
    EVENT_SEVERITY_SEVERE,
    EVENT_TYPE_AGGRESSIVE_THROTTLE,
    EVENT_TYPE_HARSH_BRAKING,
    EVENT_TYPE_SPEEDING,
    TRIP_AGGRESSIVE_DRIVING,
    TRIP_OVERSPEEDING,
    TRIP_REPEATED_HARSH_ACCELERATION,
    TRIP_REPEATED_HARSH_BRAKING,
    TRIP_UNSAFE,
    AlertConfig,
    TripAlertConfig,
    category_for,
)
from backend.alerts.generators import (
    AlertContext,
    AlertGenerator,
    make_alert,
)
from backend.alerts.models.fleet_alert import (
    AlertType,
    FleetAlert,
)
from backend.analytics.behaviour.events.event import BehaviourEvent
from backend.fleet.models.trip import Trip


class TripAlertsGenerator(AlertGenerator):
    """
    Purpose:
        Generate trip-related alerts.
    Inputs:
        AlertContext (uses trip and behaviour_events).
    Outputs:
        FleetAlert objects of type TRIP.
    """

    _AGGRESSIVE_EVENT_TYPES = frozenset(
        {
            EVENT_TYPE_HARSH_BRAKING,
            EVENT_TYPE_AGGRESSIVE_THROTTLE,
            EVENT_TYPE_SPEEDING,
        }
    )

    def __init__(
        self,
        *,
        config: AlertConfig | None = None,
    ) -> None:
        """
        Parameters
        ----------
        config:
            Alert configuration. Defaults to DEFAULT_ALERT_CONFIG.
        """
        self._config = config if config is not None else DEFAULT_ALERT_CONFIG

    @property
    def alert_type(self) -> AlertType:
        return AlertType.TRIP

    def generate(
        self,
        *,
        context: AlertContext,
    ) -> Iterable[FleetAlert]:
        """
        Generate trip alerts from context.trip and
        context.behaviour_events.

        Counts behaviour events by kind and compares them against the
        configured minimums to decide which trip alerts fire.
        """
        trip = context.trip
        events = context.behaviour_events

        if trip is None and not events:
            return ()

        counts = self._count_events(events)
        vehicle_id = trip.vehicle_id if trip is not None else events[0].vehicle_id
        driver_id = trip.driver_id if trip is not None else events[0].driver_id
        trip_id = trip.trip_id if trip is not None else events[0].trip_id
        created_at = self._trip_timestamp(trip, events)

        config: TripAlertConfig = self._config.trip
        alerts: list[FleetAlert] = []

        if counts.overspeeding >= config.overspeed_min_events:
            alerts.append(
                make_alert(
                    alert_id=TRIP_OVERSPEEDING,
                    vehicle_id=vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.overspeed_severity,
                    category=category_for(
                        TRIP_OVERSPEEDING, self.alert_type
                    ),
                    evidence=self._evidence(counts, vehicle_id, trip_id),
                    message=(
                        f"Overspeeding detected ({counts.overspeeding} "
                        "event(s))"
                    ),
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                )
            )

        if counts.harsh_braking >= config.repeated_event_min:
            alerts.append(
                make_alert(
                    alert_id=TRIP_REPEATED_HARSH_BRAKING,
                    vehicle_id=vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.repeated_harsh_braking_severity,
                    category=category_for(
                        TRIP_REPEATED_HARSH_BRAKING, self.alert_type
                    ),
                    evidence=self._evidence(counts, vehicle_id, trip_id),
                    message=(
                        "Repeated harsh braking "
                        f"({counts.harsh_braking} events)"
                    ),
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                )
            )

        if counts.harsh_acceleration >= config.repeated_event_min:
            alerts.append(
                make_alert(
                    alert_id=TRIP_REPEATED_HARSH_ACCELERATION,
                    vehicle_id=vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.repeated_harsh_acceleration_severity,
                    category=category_for(
                        TRIP_REPEATED_HARSH_ACCELERATION, self.alert_type
                    ),
                    evidence=self._evidence(counts, vehicle_id, trip_id),
                    message=(
                        "Repeated harsh acceleration "
                        f"({counts.harsh_acceleration} events)"
                    ),
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                )
            )

        if counts.severe >= config.aggressive_driving_min_severe_events:
            alerts.append(
                make_alert(
                    alert_id=TRIP_AGGRESSIVE_DRIVING,
                    vehicle_id=vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.aggressive_driving_severity,
                    category=category_for(
                        TRIP_AGGRESSIVE_DRIVING, self.alert_type
                    ),
                    evidence=self._evidence(counts, vehicle_id, trip_id),
                    message=(
                        f"Aggressive driving detected ({counts.severe} "
                        "severe event(s))"
                    ),
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                )
            )

        if counts.total >= config.unsafe_trip_min_events:
            alerts.append(
                make_alert(
                    alert_id=TRIP_UNSAFE,
                    vehicle_id=vehicle_id,
                    alert_type=self.alert_type,
                    severity=config.unsafe_trip_severity,
                    category=category_for(
                        TRIP_UNSAFE, self.alert_type
                    ),
                    evidence=self._evidence(counts, vehicle_id, trip_id),
                    message=(
                        f"Unsafe trip: {counts.total} behaviour events "
                        "recorded"
                    ),
                    created_at=created_at,
                    driver_id=driver_id,
                    trip_id=trip_id,
                )
            )

        return tuple(alerts)

    @staticmethod
    def _evidence(
        counts: "_EventCounts",
        vehicle_id: str,
        trip_id: str | None,
    ) -> dict:
        return {
            "event_counts": {
                "total": counts.total,
                "overspeeding": counts.overspeeding,
                "harsh_braking": counts.harsh_braking,
                "harsh_acceleration": counts.harsh_acceleration,
                "severe": counts.severe,
            },
            "vehicle_id": vehicle_id,
            "trip_id": trip_id,
        }

    def _count_events(
        self,
        events: tuple[BehaviourEvent, ...],
    ) -> "_EventCounts":
        return _EventCounts(
            total=len(events),
            overspeeding=sum(
                event.event_type == EVENT_TYPE_SPEEDING for event in events
            ),
            harsh_braking=sum(
                event.event_type == EVENT_TYPE_HARSH_BRAKING
                for event in events
            ),
            harsh_acceleration=sum(
                event.event_type == EVENT_TYPE_AGGRESSIVE_THROTTLE
                for event in events
            ),
            severe=sum(
                event.severity == EVENT_SEVERITY_SEVERE
                and event.event_type in self._AGGRESSIVE_EVENT_TYPES
                for event in events
            ),
        )

    @staticmethod
    def _trip_timestamp(
        trip: Trip | None,
        events: tuple[BehaviourEvent, ...],
    ) -> datetime:
        """Most representative timestamp for the trip's alerts."""
        if trip is not None:
            if trip.completed_at is not None:
                return trip.completed_at
            if trip.started_at is not None:
                return trip.started_at
        if events:
            return max(event.ended_at for event in events)
        return datetime.now(timezone.utc)


class _EventCounts:
    """Private aggregation of behaviour event counts for one trip."""

    __slots__ = ("total", "overspeeding", "harsh_braking", "harsh_acceleration", "severe")

    def __init__(
        self,
        *,
        total: int,
        overspeeding: int,
        harsh_braking: int,
        harsh_acceleration: int,
        severe: int,
    ) -> None:
        self.total = total
        self.overspeeding = overspeeding
        self.harsh_braking = harsh_braking
        self.harsh_acceleration = harsh_acceleration
        self.severe = severe
