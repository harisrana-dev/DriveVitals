from dataclasses import dataclass
from datetime import datetime

from backend.analytics.behaviour.detection.analysis import (
    DriverBehaviourAnalysis,
)
from backend.analytics.behaviour.events.event import BehaviourEvent


@dataclass
class _ActiveEvent:
    vehicle_id: str
    driver_id: str
    trip_id: str

    event_type: str
    started_at: datetime

    last_seen_at: datetime
    max_speed_excess_kmh: float
    severity: str

    started_odometer_km: float
    last_odometer_km: float


class BehaviourEventTracker:
    """
    Converts point-in-time behaviour analyses into temporal events.
    """

    _CONTINUOUS_EVENTS = (
        "speeding",
        "aggressive_throttle",
        "high_rpm",
        "harsh_braking",
    )

    def __init__(self) -> None:
        self._active_events: dict[
            tuple[str, str, str, str],
            _ActiveEvent,
        ] = {}

    def process(
        self,
        analysis: DriverBehaviourAnalysis,
        timestamp: datetime,
    ) -> list[BehaviourEvent]:
        """
        Process one behaviour analysis.

        Returns any events that became complete during this call.
        """

        completed_events: list[BehaviourEvent] = []

        for event_type in self._CONTINUOUS_EVENTS:
            active = getattr(analysis, event_type)

            key = (
                analysis.vehicle_id,
                analysis.driver_id,
                analysis.trip_id,
                event_type,
            )

            # ----------------------------------------------------------
            # EVENT START
            # ----------------------------------------------------------

            if active and key not in self._active_events:

                self._active_events[key] = _ActiveEvent(
                    vehicle_id=analysis.vehicle_id,
                    driver_id=analysis.driver_id,
                    trip_id=analysis.trip_id,
                    event_type=event_type,
                    started_at=timestamp,
                    last_seen_at=timestamp,
                    started_odometer_km=analysis.odometer_km,
                    last_odometer_km=analysis.odometer_km,
                    max_speed_excess_kmh=analysis.speed_excess_kmh,
                    severity=analysis.severity,
                )

            # ----------------------------------------------------------
            # EVENT CONTINUES
            # ----------------------------------------------------------

            elif active and key in self._active_events:

                current = self._active_events[key]

                current.last_seen_at = timestamp

                current.last_odometer_km = (
                    analysis.odometer_km
                )

                current.max_speed_excess_kmh = max(
                    current.max_speed_excess_kmh,
                    analysis.speed_excess_kmh,
                )

                current.severity = self._max_severity(
                    current.severity,
                    analysis.severity,
                )

            # ----------------------------------------------------------
            # EVENT ENDS
            # ----------------------------------------------------------

            elif (
                not active
                and key in self._active_events
            ):

                current = self._active_events.pop(key)

                completed_events.append(
                    self._complete(current)
                )

        # --------------------------------------------------------------
        # HARSH BRAKING
        #
        # Harsh braking is coalesced like any other continuous event:
        # one episode of sustained brake pressure produces exactly one
        # BehaviourEvent with a real duration and distance, instead of a
        # zero-duration event per telemetry tick.
        # --------------------------------------------------------------

        return completed_events

    def active_event_types(
        self,
        vehicle_id: str,
    ) -> tuple[str, ...]:
        """
        Return the continuous behaviour events currently active
        for one vehicle.
        """

        return tuple(
            active.event_type
            for active in self._active_events.values()
            if active.vehicle_id == vehicle_id
        )

    @staticmethod
    def _complete(
        active: _ActiveEvent,
    ) -> BehaviourEvent:
        distance_km = max(
            0.0,
            active.last_odometer_km
            - active.started_odometer_km,
        )

        duration_seconds = (
            active.last_seen_at
            - active.started_at
        ).total_seconds()

        return BehaviourEvent(
            vehicle_id=active.vehicle_id,
            driver_id=active.driver_id,
            trip_id=active.trip_id,
            event_type=active.event_type,
            started_at=active.started_at,
            ended_at=active.last_seen_at,
            duration_seconds=duration_seconds,
            distance_km=distance_km,
            max_speed_excess_kmh=active.max_speed_excess_kmh,
            severity=active.severity,
        )

    @staticmethod
    def _max_severity(
        current: str,
        incoming: str,
    ) -> str:

        ranking = {
            "normal": 0,
            "minor": 1,
            "moderate": 2,
            "severe": 3,
        }

        return (
            current
            if ranking[current] >= ranking[incoming]
            else incoming
        )

    def flush_vehicle(
        self,
        vehicle_id: str,
        timestamp: datetime,
    ) -> list[BehaviourEvent]:

        completed_events: list[BehaviourEvent] = []

        keys_to_remove = [
            key
            for key in self._active_events
            if key[0] == vehicle_id
        ]

        for key in keys_to_remove:

            active = self._active_events.pop(key)

            active.last_seen_at = timestamp

            completed_events.append(
                self._complete(active)
            )

        return completed_events

    def flush(
        self,
        timestamp: datetime,
    ) -> list[BehaviourEvent]:

        completed_events: list[BehaviourEvent] = []

        for active in self._active_events.values():

            active.last_seen_at = timestamp

            completed_events.append(
                self._complete(active)
            )

        self._active_events.clear()

        return completed_events