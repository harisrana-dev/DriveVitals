"""
Integration tests for alert lifecycle: resolve_stale_trip_alerts and
last_triggered_at.

These verify:
  * upsert sets last_triggered_at on first insert,
  * upsert updates last_triggered_at on re-trigger while preserving created_at,
  * resolve_stale_trip_alerts resolves old trip alerts,
  * resolve_stale_trip_alerts keeps recent trip alerts,
  * resolve_stale_trip_alerts skips non-trip alerts,
  * resolve_stale_trip_alerts skips already-resolved alerts,
  * resolve_stale_trip_alerts prefers last_triggered_at over created_at.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from backend.db.models.alert import Alert
from backend.db.repositories.alert_repository import AlertRepository
from backend.db.session import async_session_factory, close_db, init_db


async def _cleanup():
    async with async_session_factory() as session:
        await session.execute(delete(Alert).where(Alert.alert_type.in_(["trip", "health"])))
        await session.commit()


async def test_upsert_sets_last_triggered_on_insert():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            now = datetime.now(timezone.utc)
            row = await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Harsh accel",
                created_at=now,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()
            assert row.last_triggered_at == now
    finally:
        await _cleanup()
        await close_db()


async def test_upsert_updates_last_triggered_on_retrigger():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
            t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

            row1 = await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Harsh accel",
                created_at=t1,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()
            assert row1.last_triggered_at == t1

            row2 = await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="high",
                message="Harsh accel (worse)",
                created_at=t2,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()
            assert row2.alert_id == row1.alert_id
            assert row2.last_triggered_at == t2
            assert row2.created_at == t1
    finally:
        await _cleanup()
        await close_db()


async def test_resolve_stale_trip_alerts_resolves_old():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            old = datetime(2026, 1, 1, tzinfo=timezone.utc)
            await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Stale alert",
                created_at=old,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()

            resolved_count, resolved = await repo.resolve_stale_trip_alerts(
                stale_after_seconds=3600,
            )
            assert resolved_count == 1
            assert resolved[0].status == "resolved"
            assert resolved[0].resolved_at is not None
            await session.commit()
    finally:
        await _cleanup()
        await close_db()


async def test_resolve_stale_trip_alerts_keeps_recent():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            recent = datetime.now(timezone.utc) - timedelta(minutes=10)
            await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Recent alert",
                created_at=recent,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()

            resolved_count, _ = await repo.resolve_stale_trip_alerts(
                stale_after_seconds=3600,
            )
            assert resolved_count == 0
            await session.commit()
    finally:
        await _cleanup()
        await close_db()


async def test_resolve_stale_trip_alerts_keeps_non_trip():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            old = datetime(2026, 1, 1, tzinfo=timezone.utc)
            await repo.upsert(
                alert_id="health_battery:V-101",
                vehicle_id="V-101",
                alert_type="health",
                severity="high",
                message="Old health alert",
                created_at=old,
                condition="health_battery",
                category="vehicle_health",
            )
            await session.commit()

            resolved_count, _ = await repo.resolve_stale_trip_alerts(
                stale_after_seconds=3600,
            )
            assert resolved_count == 0
            await session.commit()
    finally:
        await _cleanup()
        await close_db()


async def test_resolve_stale_trip_alerts_keeps_already_resolved():
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            old = datetime(2026, 1, 1, tzinfo=timezone.utc)
            row = await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Already resolved",
                created_at=old,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await repo.resolve(row.alert_id)
            await session.commit()

            resolved_count, _ = await repo.resolve_stale_trip_alerts(
                stale_after_seconds=3600,
            )
            assert resolved_count == 0
            await session.commit()
    finally:
        await _cleanup()
        await close_db()


async def test_resolve_stale_trip_alerts_prefers_last_triggered():
    """When last_triggered_at is set (re-triggered recently), the alert should
    be kept even if created_at is very old."""
    await init_db()
    try:
        async with async_session_factory() as session:
            repo = AlertRepository(session)
            t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
            t2 = datetime.now(timezone.utc) - timedelta(minutes=10)

            await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="medium",
                message="Old created, recent trigger",
                created_at=t1,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()

            await repo.upsert(
                alert_id="trip_harsh_accel:V-101",
                vehicle_id="V-101",
                alert_type="trip",
                severity="high",
                message="Re-triggered",
                created_at=t2,
                condition="trip_harsh_acceleration",
                category="safety_driving",
            )
            await session.commit()

            resolved_count, _ = await repo.resolve_stale_trip_alerts(
                stale_after_seconds=3600,
            )
            assert resolved_count == 0
            await session.commit()
    finally:
        await _cleanup()
        await close_db()
