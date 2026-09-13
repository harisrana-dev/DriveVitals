"""
Integration tests for the alert-write concurrency fix.

Confirms:
  * normal alert persistence through ``PersistenceService.persist_alerts``,
  * service-level stale-trip resolution through
    ``PersistenceService.resolve_stale_trip_alerts``,
  * concurrent/overlapping alert operations run on a real PostgreSQL
    database without reproducing the previous deadlock (two transactions
    taking ShareLock on each other's ``alerts`` rows),
  * alert status transitions remain correct across the lifecycle,
  * background persistence tasks are tracked, drained on
    ``SimulationController.stop`` and cancelled on shutdown,
  * concurrent upserts of the same logical alert never create duplicate rows.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.alerts.models.fleet_alert import (
    AlertCategory,
    AlertSeverity,
    AlertType,
    FleetAlert,
)
from backend.application.simulation_controller import SimulationController
from backend.db.models.alert import Alert
from backend.db.models.vehicle import Vehicle
from backend.db.persistence_service import PersistenceService
from backend.db.session import async_session_factory, close_db, init_db
from backend.fleet.models.vehicle import Vehicle as DomainVehicle


TRIP_CONDITION = "trip_unsafe"
HEALTH_CONDITION = "health_cooling"


def _alert(
    vehicle_id: str,
    *,
    condition: str = TRIP_CONDITION,
    created_at: datetime | None = None,
    alert_type: AlertType = AlertType.TRIP,
    category: AlertCategory = AlertCategory.SAFETY_DRIVING,
) -> FleetAlert:
    return FleetAlert(
        alert_id=condition,
        vehicle_id=vehicle_id,
        alert_type=alert_type,
        severity=AlertSeverity.HIGH,
        message=f"{condition} for {vehicle_id}",
        created_at=created_at or datetime.now(timezone.utc),
        condition=condition,
        category=category,
        source="alert_engine",
    )


async def _seed_vehicle(svc: PersistenceService, vehicle_id: str) -> None:
    await svc.persist_vehicle(
        DomainVehicle(
            vehicle_id=vehicle_id,
            make="Test",
            model="Transit",
            year=2024,
            odometer_km=1000.0,
        )
    )


async def _cleanup(vehicle_ids: list[str]) -> None:
    async with async_session_factory() as session:
        await session.execute(delete(Alert).where(Alert.vehicle_id.in_(vehicle_ids)))
        await session.execute(delete(Vehicle).where(Vehicle.vehicle_id.in_(vehicle_ids)))
        await session.commit()


async def _read_alerts(vehicle_id: str) -> list[Alert]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Alert).where(Alert.vehicle_id == vehicle_id)
        )
        return list(result.scalars())


async def _read_vehicle_rows(vehicle_id: str, condition: str) -> list[Alert]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Alert).where(
                Alert.vehicle_id == vehicle_id,
                Alert.condition == condition,
            ).order_by(Alert.alert_id)
        )
        return list(result.scalars())


async def test_persist_alerts_still_works_with_lock():
    await init_db()
    svc = PersistenceService()
    vehicle_id = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, vehicle_id)
    try:
        await svc.persist_alerts([_alert(vehicle_id)])

        rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(rows) == 1
        assert rows[0].status == "active"
        assert rows[0].alert_type == "trip"
        assert rows[0].last_triggered_at is not None

        await svc.persist_alerts([_alert(vehicle_id)])
        rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(rows) == 1
        assert rows[0].status == "active"
    finally:
        await _cleanup([vehicle_id])
        await close_db()


async def test_resolve_stale_trip_alerts_service_level():
    await init_db()
    svc = PersistenceService()
    stale_vehicle = f"v-{uuid4().hex[:8]}"
    recent_vehicle = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, stale_vehicle)
    await _seed_vehicle(svc, recent_vehicle)
    try:
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        recent = datetime.now(timezone.utc) - timedelta(minutes=10)

        await svc.persist_alerts([_alert(stale_vehicle, created_at=old)])
        await svc.persist_alerts([_alert(recent_vehicle, created_at=recent)])

        resolved = await svc.resolve_stale_trip_alerts(stale_after_seconds=3600)

        stale_rows = await _read_vehicle_rows(stale_vehicle, TRIP_CONDITION)
        assert len(stale_rows) == 1
        assert stale_rows[0].status == "resolved"
        assert stale_rows[0].resolved_at is not None

        recent_rows = await _read_vehicle_rows(recent_vehicle, TRIP_CONDITION)
        assert len(recent_rows) == 1
        assert recent_rows[0].status == "active"
        assert recent_rows[0].resolved_at is None
    finally:
        await _cleanup([stale_vehicle, recent_vehicle])
        await close_db()


async def test_concurrent_persist_same_logical_alert_is_serialized():
    """Two concurrent upserts of one logical alert must converge on a single
    row. Without the single-writer gate the two sessions can both see "no
    existing row" and INSERT the same scoped id (PK collision), or update
    the same row from two open transactions."""
    await init_db()
    svc = PersistenceService()
    vehicle_id = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, vehicle_id)
    try:
        for _ in range(5):
            await asyncio.gather(
                svc.persist_alerts([_alert(vehicle_id)]),
                svc.persist_alerts([_alert(vehicle_id)]),
                svc.persist_alerts([_alert(vehicle_id)]),
            )

            rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
            assert len(rows) == 1, f"expected exactly one row, got {len(rows)}"
            assert rows[0].status == "active"
    finally:
        await _cleanup([vehicle_id])
        await close_db()


async def test_concurrent_alert_operations_no_deadlock():
    """The exact pattern behind the reported deadlock: per-vehicle
    persist_alerts + resolve_cleared_alerts racing a global
    resolve_stale_trip_alerts over overlapping alert rows.

    Under the fix, alert writes are serialized so the transactions never
    overlap; this runs against real PostgreSQL with genuinely concurrent
    asyncio tasks."""
    await init_db()
    svc = PersistenceService()
    vehicles = [f"v-{uuid4().hex[:6]}" for _ in range(4)]
    for vehicle_id in vehicles:
        await _seed_vehicle(svc, vehicle_id)

    now = datetime.now(timezone.utc)
    old = now - timedelta(hours=2)
    recent = now - timedelta(minutes=5)

    try:
        for vehicle_id in vehicles:
            await svc.persist_alerts(
                [
                    _alert(vehicle_id, condition=TRIP_CONDITION, created_at=old),
                    _alert(
                        vehicle_id,
                        condition=f"{TRIP_CONDITION}_braking",
                        created_at=old,
                    ),
                ]
            )

        async def _one_round() -> None:
            first, *rest = vehicles
            active_keys = [TRIP_CONDITION] + [
                f"{TRIP_CONDITION}_braking"
            ]
            tasks = []
            tasks.append(
                svc.persist_alerts(
                    [_alert(first, created_at=recent)]
                )
            )
            tasks.append(
                svc.persist_alerts(
                    [_alert(rest[0], created_at=recent)]
                )
            )
            for vehicle_id in rest[1:]:
                tasks.append(
                    svc.resolve_cleared_alerts(
                        vehicle_id,
                        (
                            AlertType.TRIP.value,
                            AlertType.MAINTENANCE.value,
                        ),
                        (),
                    )
                )
            tasks.append(
                svc.resolve_cleared_alerts(
                    first,
                    (
                        AlertType.TRIP.value,
                        AlertType.MAINTENANCE.value,
                    ),
                    active_keys,
                )
            )
            tasks.append(
                svc.resolve_stale_trip_alerts(stale_after_seconds=3600)
            )
            await asyncio.gather(*tasks)

        for _ in range(5):
            await _one_round()

        re_triggered = vehicles[0]
        rows = await _read_vehicle_rows(re_triggered, TRIP_CONDITION)
        active = [r for r in rows if r.status == "active"]
        assert len(active) == 1
        assert active[0].last_triggered_at >= recent

        for vehicle_id in vehicles:
            for condition in (TRIP_CONDITION, f"{TRIP_CONDITION}_braking"):
                rows = await _read_vehicle_rows(vehicle_id, condition)
                assert len(rows) <= 2, (
                    f"{vehicle_id} {condition}: expected <= 2 rows "
                    f"(resolved head + current occurrence), got {len(rows)}"
                )
                active = [r for r in rows if r.status == "active"]
                assert len(active) <= 1
    finally:
        await _cleanup(vehicles)
        await close_db()


async def test_alert_status_transitions_preserved():
    """active -> resolved (history preserved) -> new occurrence stays
    separate. The fix must not turn alerts into resolved-only or drop the
    historical row, and must not resurrect a resolved row."""
    await init_db()
    svc = PersistenceService()
    vehicle_id = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, vehicle_id)
    try:
        old = datetime.now(timezone.utc) - timedelta(hours=2)

        await svc.persist_alerts([_alert(vehicle_id, created_at=old)])
        resolved = await svc.resolve_stale_trip_alerts(stale_after_seconds=3600)
        assert resolved == 1

        historical = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(historical) == 1
        assert historical[0].status == "resolved"
        assert historical[0].resolved_at is not None

        await svc.persist_alerts([_alert(vehicle_id)])
        rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(rows) == 2
        assert {r.status for r in rows} == {"active", "resolved"}
        active = next(r for r in rows if r.status == "active")
        assert active.resolved_at is None
    finally:
        await _cleanup([vehicle_id])
        await close_db()


async def test_background_tasks_tracked_drained_and_cancelled():
    await init_db()
    svc = PersistenceService()
    vehicle_id = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, vehicle_id)
    try:
        task = svc.schedule_background(svc.persist_alerts([_alert(vehicle_id)]))
        assert task in svc._background_tasks
        await svc.drain_background_tasks()
        await asyncio.sleep(0)
        assert task.done()
        assert not task.cancelled()
        assert task not in svc._background_tasks
        rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(rows) == 1

        blocked = asyncio.Event()
        async def _never_finishes():
            await blocked.wait()

        pending = svc.schedule_background(_never_finishes())
        assert pending in svc._background_tasks
        svc.cancel_background_tasks()
        try:
            await pending
        except asyncio.CancelledError:
            pass
        await asyncio.sleep(0)
        assert pending.cancelled()
        assert pending not in svc._background_tasks
    finally:
        await _cleanup([vehicle_id])
        await close_db()


class _StubRuntime:
    """Minimal runtime facade used to exercise SimulationController.stop
    without starting a full fleet loop."""

    def __init__(self, persistence: PersistenceService) -> None:
        self._persistence = persistence
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True

    @property
    def persistence_service(self) -> PersistenceService | None:
        return self._persistence


async def test_simulation_stop_drains_background_tasks():
    """Online alert writes scheduled by the runtime are drained by
    SimulationController.stop so a subsequent launch cannot race writers
    from the previous run."""
    await init_db()
    svc = PersistenceService()
    vehicle_id = f"v-{uuid4().hex[:8]}"
    await _seed_vehicle(svc, vehicle_id)
    try:
        controller = SimulationController(_StubRuntime(svc))

        for _ in range(5):
            svc.schedule_background(svc.persist_alerts([_alert(vehicle_id)]))
            svc.schedule_background(
                svc.resolve_stale_trip_alerts(stale_after_seconds=3600)
            )

        status = await controller.stop()
        assert status["running"] is False
        await asyncio.sleep(0)
        assert len(svc._background_tasks) == 0

        rows = await _read_vehicle_rows(vehicle_id, TRIP_CONDITION)
        assert len(rows) == 1
        assert rows[0].status == "active"
    finally:
        await _cleanup([vehicle_id])
        await close_db()


async def test_shutdown_cancels_background_tasks():
    await init_db()
    svc = PersistenceService()
    try:
        blocked = asyncio.Event()

        async def _pending_forever():
            await blocked.wait()

        task = svc.schedule_background(_pending_forever())
        assert task in svc._background_tasks

        controller = SimulationController(_StubRuntime(svc))
        controller.shutdown()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await asyncio.sleep(0)
        assert task.cancelled()
        assert task not in svc._background_tasks
    finally:
        await close_db()