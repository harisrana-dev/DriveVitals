"""
WebSocket trip-snapshot contract tests.

The Trips WebSocket and the trips REST API must expose the same canonical
trip payload: field names (``fuel_consumed_liters``, ``safety_score``,
``grade``, ``started_at``/``completed_at``), a first-class ``status``, and
the derived behaviour counts/durations/severity.
"""

from datetime import datetime, timezone

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
from backend.fleet.models.trip import (
    Trip,
    TripStatus,
)
from backend.trips.services.trip_builder import (
    TripBuilder,
)


def _summary() -> DriverBehaviourSummary:
    return DriverBehaviourSummary(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        total_distance_km=5.0,
        speeding_event_count=1,
        speeding_duration_seconds=20.0,
        speeding_distance_km=0.5,
        maximum_speed_excess_kmh=10.0,
        harsh_braking_count=1,
        aggressive_throttle_event_count=1,
        aggressive_throttle_duration_seconds=8.0,
        high_rpm_event_count=0,
        high_rpm_duration_seconds=0.0,
        severe_event_count=0,
        moderate_event_count=2,
        minor_event_count=1,
        overall_severity="moderate",
    )


def _context() -> AnalyticsContext:
    return AnalyticsContext(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        route_id="R-1",
        route_type="urban",
        speed_limit_kmh=60.0,
        vehicle_make="Ford",
        vehicle_model="Transit",
        vehicle_year=2023,
        driver_name="Alice Smith",
        route_name="Warehouse to Customer A",
    )


def _runtime_state() -> RuntimeAnalyticsState:
    return RuntimeAnalyticsState(
        vehicle_id="V-1",
        driver_id="D-1",
        trip_id="T-1",
        timestamp=datetime(2026, 8, 7, 10, 6, tzinfo=timezone.utc),
        speed_kmh=50.0,
        rpm=2200.0,
        throttle_position_percent=40.0,
        brake_pressure=0.1,
        coolant_temperature_c=90.0,
        engine_load_percent=60.0,
        fuel_rate_lph=6.0,
        fuel_level_percent=50.0,
        odometer_km=1010.0,
    )


def _events() -> list[BehaviourEvent]:
    return [
        BehaviourEvent(
            vehicle_id="V-1",
            driver_id="D-1",
            trip_id="T-1",
            event_type="speeding",
            started_at=datetime(2026, 8, 7, 10, 2, tzinfo=timezone.utc),
            ended_at=datetime(2026, 8, 7, 10, 2, 20, tzinfo=timezone.utc),
            duration_seconds=20.0,
            distance_km=0.5,
            severity="moderate",
            max_speed_excess_kmh=10.0,
        ),
        BehaviourEvent(
            vehicle_id="V-1",
            driver_id="D-1",
            trip_id="T-1",
            event_type="aggressive_throttle",
            started_at=datetime(2026, 8, 7, 10, 4, tzinfo=timezone.utc),
            ended_at=datetime(2026, 8, 7, 10, 4, 8, tzinfo=timezone.utc),
            duration_seconds=8.0,
            distance_km=0.2,
            severity="minor",
            max_throttle_percent=92.0,
        ),
    ]


def _trip() -> Trip:
    return Trip(
        trip_id="T-1",
        vehicle_id="V-1",
        driver_id="D-1",
        route_id="R-1",
        status=TripStatus.COMPLETED,
        started_at=datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 8, 7, 10, 6, tzinfo=timezone.utc),
        distance_travelled_km=5.0,
        fuel_used_liters=0.4,
    )


class TestTripSnapshotContract:

    def test_completed_snapshot_uses_canonical_fields(self) -> None:
        snapshot = TripBuilder().build(
            _summary(),
            _context(),
            _runtime_state(),
            _events(),
            _trip(),
        )

        assert snapshot.trip_id == "T-1"
        assert snapshot.status == "completed"
        assert snapshot.vehicle_name == "2023 Ford Transit"
        assert snapshot.driver_name == "Alice Smith"
        assert snapshot.route_id == "R-1"
        assert snapshot.route_name == "Warehouse to Customer A"
        assert snapshot.route_type == "urban"
        assert snapshot.started_at == datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)
        assert snapshot.completed_at == datetime(2026, 8, 7, 10, 6, tzinfo=timezone.utc)

        assert snapshot.distance_km == 5.0
        assert snapshot.duration_seconds == 360.0
        assert snapshot.fuel_consumed_liters == 0.4
        assert snapshot.average_fuel_rate_lph == 4.0
        assert snapshot.safety_score > 0.0
        assert snapshot.grade in {"A", "B", "C", "D", "F"}

        assert snapshot.speeding_event_count == 1
        assert snapshot.speeding_duration_seconds == 20.0
        assert snapshot.harsh_braking_count == 1
        assert snapshot.aggressive_throttle_event_count == 1
        assert snapshot.aggressive_throttle_duration_seconds == 8.0
        assert snapshot.moderate_event_count == 2
        assert snapshot.minor_event_count == 1
        assert snapshot.overall_severity == "moderate"

        assert len(snapshot.events) == 2
        assert snapshot.events[0]["event_type"] == "speeding"
        assert snapshot.events[0]["severity"] == "moderate"
        assert snapshot.events[0]["duration_seconds"] == 20.0
        assert "label" in snapshot.events[0]

    def test_snapshot_status_reflects_trip_status(self) -> None:
        trip = _trip()
        trip.status = TripStatus.IN_PROGRESS

        snapshot = TripBuilder().build(
            _summary(),
            _context(),
            _runtime_state(),
            [],
            trip,
        )

        assert snapshot.status == "in_progress"

    def test_snapshot_without_trip_defaults_to_completed(self) -> None:
        snapshot = TripBuilder().build(
            _summary(),
            _context(),
            _runtime_state(),
            [],
            None,
        )

        assert snapshot.status == "completed"
        assert snapshot.started_at is None
        assert snapshot.completed_at == _runtime_state().timestamp

    def test_snapshot_maximum_speed_is_observed_peak_not_heuristic(self) -> None:
        trip = _trip()
        trip.maximum_speed_kmh = 88.5

        snapshot = TripBuilder().build(
            _summary(),
            _context(),
            _runtime_state(),
            _events(),
            trip,
        )

        # The summary carries maximum_speed_excess_kmh=10.0 against a
        # 60.0 km/h limit (heuristic would give 70.0). The snapshot must
        # report the observed peak recorded on the trip instead.
        assert snapshot.maximum_speed_kmh == 88.5

    def test_snapshot_without_trip_reports_zero_maximum_speed(self) -> None:
        snapshot = TripBuilder().build(
            _summary(),
            _context(),
            _runtime_state(),
            [],
            None,
        )

        assert snapshot.maximum_speed_kmh == 0.0
