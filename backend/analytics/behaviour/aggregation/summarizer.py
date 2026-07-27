from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.behaviour.events.event import BehaviourEvent


class DriverBehaviourSummarizer:
    """
    Aggregates completed behaviour events into a trip-level summary.
    """

    def summarize(
        self,
        *,
        vehicle_id: str,
        driver_id: str,
        trip_id: str,
        total_distance_km: float,
        events: list[BehaviourEvent],
    ) -> DriverBehaviourSummary:

        speeding_events = [
            event
            for event in events
            if event.event_type == "speeding"
        ]

        harsh_braking_events = [
            event
            for event in events
            if event.event_type == "harsh_braking"
        ]

        aggressive_throttle_events = [
            event
            for event in events
            if event.event_type == "aggressive_throttle"
        ]

        high_rpm_events = [
            event
            for event in events
            if event.event_type == "high_rpm"
        ]

        return DriverBehaviourSummary(
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
            total_distance_km=total_distance_km,
            speeding_event_count=len(speeding_events),
            speeding_duration_seconds=sum(
                event.duration_seconds
                for event in speeding_events
            ),
            speeding_distance_km=0.0,
            maximum_speed_excess_kmh=max(
                (
                    event.max_speed_excess_kmh
                    for event in speeding_events
                ),
                default=0.0,
            ),
            harsh_braking_count=len(
                harsh_braking_events
            ),
            aggressive_throttle_event_count=len(
                aggressive_throttle_events
            ),
            aggressive_throttle_duration_seconds=sum(
                event.duration_seconds
                for event in aggressive_throttle_events
            ),
            high_rpm_event_count=len(
                high_rpm_events
            ),
            high_rpm_duration_seconds=sum(
                event.duration_seconds
                for event in high_rpm_events
            ),
            severe_event_count=sum(
                event.severity == "severe"
                for event in events
            ),
            moderate_event_count=sum(
                event.severity == "moderate"
                for event in events
            ),
            minor_event_count=sum(
                event.severity == "minor"
                for event in events
            ),
            overall_severity=self._determine_overall_severity(
                events
            ),
        )

    @staticmethod
    def _determine_overall_severity(
        events: list[BehaviourEvent],
    ) -> str:

        if any(
            event.severity == "severe"
            for event in events
        ):
            return "severe"

        if any(
            event.severity == "moderate"
            for event in events
        ):
            return "moderate"

        if any(
            event.severity == "minor"
            for event in events
        ):
            return "minor"

        return "normal"