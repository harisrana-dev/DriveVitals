import asyncio
import time
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from starlette.testclient import TestClient

import backend.api.main as main
import backend.api.websocket.trips as trips_module
from backend.alerts.models.fleet_alert import (
    AlertCategory,
    AlertSeverity,
    AlertType,
    FleetAlert,
)
from backend.analytics.behaviour.aggregation.summary import (
    DriverBehaviourSummary,
)
from backend.analytics.context.analytics_context import AnalyticsContext
from backend.analytics.state.runtime_state import (
    RuntimeAnalyticsState,
)
from backend.api.main import app
from backend.api.websocket.trip_publisher import (
    TripSnapshotPublisher,
)
from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import BehaviorProfile, Driver
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.trips.schemas.trip_payload import (
    TripSnapshot,
    TripsSnapshot,
)
from backend.trips.services.trip_builder import TripBuilder
from backend.trips.store.trip_store import TripStore


class TestWebSockets:

    def test_dashboard_websocket_connects(self) -> None:
        client = TestClient(app)

        with client.websocket_connect("/ws/dashboard") as websocket:
            websocket.send_text("ping")

    def test_trips_websocket_connects(self) -> None:
        client = TestClient(app)

        with client.websocket_connect("/ws/trips") as websocket:
            websocket.send_text("ping")

    def test_alerts_websocket_connects(self) -> None:
        client = TestClient(app)

        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.send_text("ping")


class TestAlertsLifecycleWiring:
    """Regression for the FastAPI startup crash.

    The Alerts page wiring in ``backend/api/main.py`` originally called
    ``runtime.persistence.set_alert_event_callback(...)`` during lifespan
    startup, but ``DriveVitalsRuntime`` stores its persistence service as
    the private ``_persistence_service`` attribute and exposes no
    ``.persistence`` attribute, so startup raised ``AttributeError``.

    The alert-event callback is owned by the shared ``PersistenceService``
    instance that ``backend/api/main.py`` constructs for the runtime. The
    lifespan must register the callback on that same instance and wire it to
    the alerts WebSocket queue.

    ``TestClient.websocket_connect`` alone does not run the app lifespan, so
    this test drives the real ``lifespan`` async generator directly. The
    heavy ``runtime.run`` loop is stubbed out so the test stays fast,
    deterministic and touches no real database.
    """

    def test_lifespan_wires_alert_callback_to_alerts_queue(self) -> None:
        async def _scenario() -> None:
            from backend.api.websocket import alerts as alerts_module

            manager = _RecordingManager()
            original_manager = alerts_module.websocket_manager
            alerts_module.websocket_manager = manager

            async def _noop() -> None:
                return None

            gen = None
            try:
                with patch.object(main.runtime, "run", _noop):
                    # Drain any alert events other tests enqueued into the
                    # shared module-level queue while no worker was running,
                    # so this test only observes the event it emits.
                    while not main.alerts_queue.empty():
                        with suppress(asyncio.QueueEmpty):
                            main.alerts_queue.get_nowait()

                    gen = main.lifespan(main.app)
                    try:
                        # Start lifespan. Regression (AttributeError on
                        # runtime.persistence) surfaces here.
                        await gen.__aenter__()

                        # The callback must be registered on the shared
                        # persistence service instance and point at the
                        # alerts WebSocket queue.
                        callback = main.persistence_service._alert_event_callback
                        assert callback == main.alerts_queue.put_nowait
                        assert callback.__self__ is main.alerts_queue

                        # End to end: an emitted alert lifecycle event is
                        # serialized, queued by the callback, drained by the
                        # alerts worker and broadcast to connected clients.
                        alert = FleetAlert(
                            alert_id="trip_unsafe:v-101",
                            vehicle_id="v-101",
                            driver_id="d-7",
                            trip_id="t-9",
                            alert_type=AlertType.TRIP,
                            severity=AlertSeverity.CRITICAL,
                            message="Harsh braking detected on route",
                            created_at=datetime.now(timezone.utc),
                            condition="trip_unsafe",
                            category=AlertCategory.SAFETY_DRIVING,
                            evidence={"event_counts": {"harsh_braking": 3}},
                        )
                        main.persistence_service._emit_alert_event(
                            "alert_created",
                            alert,
                            stored_alert_id="trip_unsafe:v-101",
                        )

                        deadline = time.monotonic() + 1.0
                        while not manager.messages and time.monotonic() < deadline:
                            await asyncio.sleep(0.01)

                        assert len(manager.messages) == 1
                        event = manager.messages[0]
                        assert event["type"] == "alert_event"
                        data = event["data"]
                        assert data["alert_id"] == "trip_unsafe:v-101"
                        assert data["condition"] == "trip_unsafe"
                        assert data["category"] == "safety_driving"
                        assert data["severity"] == "critical"
                        assert data["message"] == "Harsh braking detected on route"
                    finally:
                        # Drive shutdown (cancels the lifespan's worker and
                        # runtime tasks). Idempotent if startup failed and
                        # closed the generator.
                        if gen is not None:
                            with suppress(StopAsyncIteration, RuntimeError):
                                await gen.__aexit__(None, None, None)
            finally:
                alerts_module.websocket_manager = original_manager

        asyncio.run(_scenario())


class _RecordingManager:
    """WebSocketManager stand-in that records every broadcast."""

    def __init__(self):
        self.messages = []

    async def broadcast(self, message: dict) -> None:
        self.messages.append(message)


class _StubPersistence:
    async def _noop(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return self._noop


class _FastSleep:
    def __enter__(self):
        self._real_sleep = asyncio.sleep

        async def fast_sleep(_delay):
            await self._real_sleep(0)

        asyncio.sleep = fast_sleep
        return self

    def __exit__(self, *exc):
        asyncio.sleep = self._real_sleep


def _make_context(vehicle_id, driver_id, trip_id, route_id):
    return AnalyticsContext(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        route_id=route_id,
        route_type="urban",
        speed_limit_kmh=60.0,
        route_name="Warehouse \u2192 Customer A",
        vehicle_make="Ford",
        vehicle_model="Transit",
        vehicle_year=2023,
        driver_name="Test Driver",
    )


def _make_summary(vehicle_id, driver_id, trip_id, distance_km):
    return DriverBehaviourSummary(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        total_distance_km=distance_km,
        speeding_event_count=0,
        speeding_duration_seconds=0.0,
        speeding_distance_km=0.0,
        maximum_speed_excess_kmh=0.0,
        harsh_braking_count=0,
        aggressive_throttle_event_count=0,
        aggressive_throttle_duration_seconds=0.0,
        high_rpm_event_count=0,
        high_rpm_duration_seconds=0.0,
        severe_event_count=0,
        moderate_event_count=0,
        minor_event_count=0,
        overall_severity="none",
    )


def _make_runtime_state(vehicle_id, driver_id, trip_id, timestamp, speed_kmh=48.0):
    return RuntimeAnalyticsState(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        trip_id=trip_id,
        timestamp=timestamp,
        speed_kmh=speed_kmh,
        rpm=2200.0,
        throttle_position_percent=35.0,
        brake_pressure=0.0,
        coolant_temperature_c=87.0,
        engine_load_percent=40.0,
        fuel_rate_lph=5.5,
        fuel_level_percent=72.0,
        odometer_km=1000.0,
    )


def _active_trip_snapshot(trip_id, started_at, now, distance_km, speed_kmh):
    duration_seconds = (now - started_at).total_seconds()
    return TripSnapshot(
        trip_id=trip_id,
        status="in_progress",
        vehicle_id="V-1",
        driver_id="D-1",
        vehicle_name="2023 Ford Transit",
        driver_name="Test Driver",
        route_id="R-1",
        route_type="urban",
        route_name="Warehouse \u2192 Customer A",
        distance_km=distance_km,
        duration_seconds=duration_seconds,
        average_speed_kmh=round(distance_km / (duration_seconds / 3600), 2),
        maximum_speed_kmh=0.0,
        fuel_consumed_liters=0.5,
        average_fuel_rate_lph=6.0,
        safety_score=None,
        grade=None,
        started_at=started_at,
        completed_at=None,
        speeding_event_count=0,
        speeding_duration_seconds=0.0,
        harsh_braking_count=0,
        aggressive_throttle_event_count=0,
        aggressive_throttle_duration_seconds=0.0,
        high_rpm_event_count=0,
        high_rpm_duration_seconds=0.0,
        severe_event_count=0,
        moderate_event_count=0,
        minor_event_count=0,
        overall_severity="normal",
        events=(),
        current_speed_kmh=speed_kmh,
        speeding=False,
        harsh_braking=False,
        aggressive_throttle=False,
        high_rpm=False,
    )


def _trips_snapshot(timestamp, trips):
    return TripsSnapshot(
        timestamp=timestamp,
        trips=tuple(trips),
        total_trips=len(trips),
        total_distance_km=sum(t.distance_km for t in trips),
        average_safety_score=0.0,
        total_fuel_consumed_liters=0.0,
    )


def _build_fleet(specs, tick_seconds=1.0):
    fleet = FleetRunner(tick_seconds=tick_seconds)
    trips = []
    for vid, did, rid, tid, fuel, distance in specs:
        vehicle = Vehicle(
            vehicle_id=vid,
            make="Ford",
            model="Transit",
            year=2023,
            odometer_km=1000.0,
            fuel_level_percent=fuel,
        )
        driver = Driver(
            driver_id=did,
            name="Test Driver",
            behavior_profile=BehaviorProfile.CAUTIOUS,
        )
        route = Route(
            route_id=rid,
            origin="Warehouse",
            destination="Customer A",
            distance_km=distance,
            route_type=RouteType.URBAN,
            speed_limit_kmh=60.0,
        )
        trip = Trip(
            trip_id=tid,
            vehicle_id=vid,
            driver_id=did,
            route_id=rid,
        )
        trips.append(trip)
        fleet.add_assignment(
            assignment=Assignment(
                assignment_id=f"A-{vid}",
                driver_id=did,
                vehicle_id=vid,
                route_id=rid,
            ),
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )
    return fleet, trips


def _drain_pending_tasks():
    return asyncio.gather(
        *[t for t in asyncio.all_tasks() if t is not asyncio.current_task()],
        return_exceptions=True,
    )


class TestTripsStreamMessages:
    """Message-level contract for the /ws/trips stream.

    Uses a dedicated queue, worker and recording manager so the module
    singletons used by the real app are never polluted, and drives the
    worker deterministically with ``queue.join()``.
    """

    def test_worker_serializes_active_snapshot_contract(self) -> None:
        async def _scenario():
            queue = asyncio.Queue()
            manager = _RecordingManager()
            original_manager = trips_module.websocket_manager
            original_queue = trips_module.trips_queue
            trips_module.websocket_manager = manager
            trips_module.trips_queue = queue
            worker = None
            try:
                worker = asyncio.create_task(trips_module.trips_worker())
                await asyncio.sleep(0)

                started = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)
                now = started + timedelta(minutes=5)
                snap = _active_trip_snapshot("T-1", started, now, 3.0, 48.0)
                queue.put_nowait(_trips_snapshot(now, [snap]))
                await queue.join()
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
                trips_module.websocket_manager = original_manager
                trips_module.trips_queue = original_queue

            assert len(manager.messages) == 1
            message = manager.messages[0]
            assert message["type"] == "trips_snapshot"

            data = message["data"]
            assert data["timestamp"] == now.isoformat()
            assert data["total_trips"] == 1
            assert data["average_safety_score"] == 0.0
            assert data["total_fuel_consumed_liters"] == 0.0

            trip = data["trips"][0]
            assert trip["trip_id"] == "T-1"
            assert trip["status"] == "in_progress"
            assert trip["started_at"] == started.isoformat()
            assert trip["completed_at"] is None
            assert trip["safety_score"] is None
            assert trip["grade"] is None
            assert trip["distance_km"] == 3.0
            assert trip["duration_seconds"] == 300.0
            assert trip["current_speed_kmh"] == 48.0
            assert trip["speeding"] is False
            assert trip["harsh_braking"] is False
            assert trip["aggressive_throttle"] is False
            assert trip["high_rpm"] is False

            # M1 contract: unified field names only, no legacy names.
            assert "trip_score" not in trip
            assert "fuel_used_liters" not in trip
            assert "start_time" not in trip
            assert "end_time" not in trip
            assert "brake_pressure" not in trip
            assert "current_speed_kmh" in trip
            assert "speeding" in trip
            assert "harsh_braking" in trip
            assert "aggressive_throttle" in trip
            assert "high_rpm" in trip

        asyncio.run(_scenario())

    def test_worker_broadcasts_successive_active_updates(self) -> None:
        async def _scenario():
            queue = asyncio.Queue()
            manager = _RecordingManager()
            original_manager = trips_module.websocket_manager
            original_queue = trips_module.trips_queue
            trips_module.websocket_manager = manager
            trips_module.trips_queue = queue
            worker = None
            try:
                worker = asyncio.create_task(trips_module.trips_worker())
                await asyncio.sleep(0)

                started = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)
                for i in range(3):
                    now = started + timedelta(seconds=(i + 1) * 60)
                    snap = _active_trip_snapshot(
                        "T-1",
                        started,
                        now,
                        distance_km=2.0 + i * 1.5,
                        speed_kmh=40.0 + i * 5.0,
                    )
                    queue.put_nowait(_trips_snapshot(now, [snap]))
                await queue.join()
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
                trips_module.websocket_manager = original_manager
                trips_module.trips_queue = original_queue

            assert len(manager.messages) == 3
            for message in manager.messages:
                data = message["data"]
                assert data["total_trips"] == 1
                assert [t["trip_id"] for t in data["trips"]] == ["T-1"]
                assert len({t["trip_id"] for t in data["trips"]}) == 1

            distances = [
                message["data"]["trips"][0]["distance_km"]
                for message in manager.messages
            ]
            durations = [
                message["data"]["trips"][0]["duration_seconds"]
                for message in manager.messages
            ]
            speeds = [
                message["data"]["trips"][0]["current_speed_kmh"]
                for message in manager.messages
            ]
            assert distances == [2.0, 3.5, 5.0]
            assert durations == [60.0, 120.0, 180.0]
            assert speeds == [40.0, 45.0, 50.0]

        asyncio.run(_scenario())

    def test_completed_publish_broadcasts_full_store(self) -> None:
        async def _scenario():
            queue = asyncio.Queue()
            manager = _RecordingManager()
            store = TripStore()
            publisher = TripSnapshotPublisher(
                queue=queue,
                builder=TripBuilder(),
                store=store,
            )
            original_manager = trips_module.websocket_manager
            original_queue = trips_module.trips_queue
            trips_module.websocket_manager = manager
            trips_module.trips_queue = queue
            worker = None
            try:
                worker = asyncio.create_task(trips_module.trips_worker())
                await asyncio.sleep(0)

                started = datetime(2026, 8, 7, 10, 0, tzinfo=timezone.utc)
                completed_at = started + timedelta(minutes=10)
                trip = Trip(
                    trip_id="T-1",
                    vehicle_id="V-1",
                    driver_id="D-1",
                    route_id="R-1",
                    status=TripStatus.COMPLETED,
                    started_at=started,
                    completed_at=completed_at,
                    distance_travelled_km=5.0,
                    fuel_used_liters=1.5,
                )
                context = _make_context("V-1", "D-1", "T-1", "R-1")
                runtime_state = _make_runtime_state(
                    "V-1", "D-1", "T-1", completed_at
                )
                summary = _make_summary("V-1", "D-1", "T-1", 5.0)

                publisher.publish(summary, context, runtime_state, [], trip)
                await queue.join()
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
                trips_module.websocket_manager = original_manager
                trips_module.trips_queue = original_queue

            assert len(store) == 1
            assert len(manager.messages) == 1
            data = manager.messages[0]["data"]
            assert data["total_trips"] == 1

            trip_data = data["trips"][0]
            assert trip_data["trip_id"] == "T-1"
            assert trip_data["status"] == "completed"
            assert trip_data["started_at"] == started.isoformat()
            assert trip_data["completed_at"] == completed_at.isoformat()
            assert trip_data["safety_score"] is not None
            assert trip_data["grade"] in {"A", "B", "C", "D", "F"}
            assert trip_data["distance_km"] == 5.0
            assert trip_data["fuel_consumed_liters"] == 1.5
            assert data["average_safety_score"] == trip_data["safety_score"]
            assert data["total_fuel_consumed_liters"] == 1.5

        asyncio.run(_scenario())

    def test_runtime_active_stream_reaches_websocket(self) -> None:
        """End to end: runtime tick -> publisher -> trips worker -> broadcast.

        Uses three long routes so no trip completes, keeping the active
        stream stable while three per-tick batches are asserted.
        """

        async def _scenario():
            queue = asyncio.Queue()
            manager = _RecordingManager()
            original_manager = trips_module.websocket_manager
            original_queue = trips_module.trips_queue
            trips_module.websocket_manager = manager
            trips_module.trips_queue = queue
            worker = None
            try:
                runtime = DriveVitalsRuntime(
                    tick_seconds=1.0,
                    persistence_service=_StubPersistence(),
                )
                specs = [
                    ("V-1", "D-1", "R-1", "T-1", 90.0, 50.0),
                    ("V-2", "D-2", "R-2", "T-2", 80.0, 50.0),
                    ("V-3", "D-3", "R-3", "T-3", 70.0, 50.0),
                ]
                for vid, did, rid, tid, _fuel, _distance in specs:
                    runtime._context_store.register(
                        _make_context(vid, did, tid, rid)
                    )
                fleet, trips = _build_fleet(specs)
                runtime._fleet = fleet

                publisher = TripSnapshotPublisher(
                    queue=queue,
                    builder=SimpleNamespace(),
                    store=SimpleNamespace(),
                )
                ticks = {"n": 0}

                def on_update(snapshots, now):
                    publisher.publish_active(snapshots, now)
                    ticks["n"] += 1
                    if ticks["n"] >= 3:
                        runtime.stop()

                runtime.set_trip_update_callback(on_update)

                worker = asyncio.create_task(trips_module.trips_worker())
                await asyncio.sleep(0)

                with _FastSleep():
                    await runtime.run()

                await queue.join()
            finally:
                if worker is not None:
                    worker.cancel()
                    with suppress(asyncio.CancelledError):
                        await worker
                trips_module.websocket_manager = original_manager
                trips_module.trips_queue = original_queue
                await _drain_pending_tasks()

            messages = manager.messages
            assert len(messages) >= 3

            for message in messages:
                assert message["type"] == "trips_snapshot"
                data = message["data"]
                assert data["total_trips"] == len(data["trips"])
                trip_ids = [t["trip_id"] for t in data["trips"]]
                assert len(trip_ids) == len(set(trip_ids))
                assert len(trip_ids) <= 3
                for t in data["trips"]:
                    assert t["status"] == "in_progress"
                    assert t["completed_at"] is None
                    assert t["safety_score"] is None
                    assert t["grade"] is None
                    assert t["started_at"] is not None
                    assert t["current_speed_kmh"] is not None
                    assert t["current_speed_kmh"] >= 0.0

            # A recurring trip grows across successive active batches.
            first_trip_id = messages[0]["data"]["trips"][0]["trip_id"]
            distances = [
                t["distance_km"]
                for message in messages
                for t in message["data"]["trips"]
                if t["trip_id"] == first_trip_id
            ]
            assert len(distances) >= 3
            assert distances[0] < distances[-1]
            assert all(
                distances[i] < distances[i + 1]
                for i in range(len(distances) - 1)
            )

        asyncio.run(_scenario())
