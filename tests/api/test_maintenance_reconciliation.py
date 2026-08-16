"""
Repository-level tests for the maintenance data-trust phase.

Covers the semantics that make the maintenance page truthful without a
second data model:

- upsert keeps exactly one *pending* row per (vehicle_id, maintenance_type),
  whether the surviving row uses a canonical or a legacy identity;
- upsert never resurrects a completed row (history stays history);
- ``created_at`` is the real creation time and is never overwritten by an
  update, while ``due_date`` carries the projected service date;
- ``complete`` is idempotent and records the completion odometer;
- ``reconcile_duplicates`` removes legacy duplicate pending projections and
  is itself idempotent.
"""

from datetime import datetime, timezone

from sqlalchemy import select

from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.repositories.maintenance_repository import (
    MaintenanceRepository,
)

NOWISH_TOLERANCE_SECONDS = 60


async def _pending_for(
    session,
    vehicle_id: str,
    maintenance_type: str,
) -> list[MaintenanceRecord]:
    result = await session.execute(
        select(MaintenanceRecord).where(
            MaintenanceRecord.vehicle_id == vehicle_id,
            MaintenanceRecord.maintenance_type == maintenance_type,
            MaintenanceRecord.status == "pending",
        )
    )
    return list(result.scalars())


class TestMaintenanceUpsert:

    async def test_upsert_records_created_at_now_and_due_date(
        self, session
    ) -> None:
        repo = MaintenanceRepository(session)
        row = await repo.upsert(
            maintenance_id="v-3:coolant_flush",
            vehicle_id="v-3",
            maintenance_type="coolant_flush",
            priority="medium",
            due_odometer_km=5000.0,
            due_date=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
            component="cooling",
            reason="coolant aged",
            recommended_action="flush the coolant",
            estimated_cost=120.0,
        )
        await session.commit()

        assert row.due_date == datetime(
            2026, 5, 1, 9, 0, tzinfo=timezone.utc
        )
        assert row.component == "cooling"
        assert row.reason == "coolant aged"
        assert row.recommended_action == "flush the coolant"
        assert row.estimated_cost == 120.0
        assert row.status == "pending"
        delta = abs((row.created_at - datetime.now(timezone.utc)).total_seconds())
        assert delta < NOWISH_TOLERANCE_SECONDS

    async def test_upsert_updates_pending_row_without_resetting_created_at(
        self, session
    ) -> None:
        repo = MaintenanceRepository(session)
        first = await repo.upsert(
            maintenance_id="v-3:coolant_flush",
            vehicle_id="v-3",
            maintenance_type="coolant_flush",
            priority="medium",
            due_odometer_km=5000.0,
            due_date=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
        )
        await session.commit()
        original_created_at = first.created_at

        second = await repo.upsert(
            maintenance_id="v-3:coolant_flush",
            vehicle_id="v-3",
            maintenance_type="coolant_flush",
            priority="high",
            due_odometer_km=4500.0,
            due_date=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        )
        await session.commit()

        assert second.maintenance_id == first.maintenance_id
        assert second.created_at == original_created_at
        assert second.priority == "high"
        assert second.due_odometer_km == 4500.0

    async def test_upsert_updates_legacy_pending_row(self, session) -> None:
        repo = MaintenanceRepository(session)
        session.add(
            MaintenanceRecord(
                maintenance_id="v-3:oil_change:9000",
                vehicle_id="v-3",
                maintenance_type="oil_change",
                priority="medium",
                status="pending",
                due_odometer_km=9000.0,
                created_at=datetime(
                    2026, 1, 5, 9, 0, tzinfo=timezone.utc
                ),
            )
        )
        await session.flush()

        row = await repo.upsert(
            maintenance_id="v-3:oil_change",
            vehicle_id="v-3",
            maintenance_type="oil_change",
            priority="medium",
            due_odometer_km=8500.0,
            due_date=datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc),
        )
        await session.commit()

        assert row.maintenance_id == "v-3:oil_change:9000"
        assert row.due_odometer_km == 8500.0
        pending = await _pending_for(session, "v-3", "oil_change")
        assert len(pending) == 1

    async def test_upsert_mints_fresh_id_after_completion(self, session) -> None:
        repo = MaintenanceRepository(session)
        await repo.upsert(
            maintenance_id="v-3:brake_pad_replacement",
            vehicle_id="v-3",
            maintenance_type="brake_pad_replacement",
            priority="medium",
            due_odometer_km=9000.0,
        )
        await session.commit()

        completed = await repo.complete(
            "v-3:brake_pad_replacement", completed_odometer_km=9000.0
        )
        assert completed is not None
        assert completed.status == "completed"
        await session.commit()

        new_pending = await repo.upsert(
            maintenance_id="v-3:brake_pad_replacement",
            vehicle_id="v-3",
            maintenance_type="brake_pad_replacement",
            priority="medium",
            due_odometer_km=18000.0,
        )
        await session.commit()

        assert new_pending.maintenance_id != "v-3:brake_pad_replacement"
        assert new_pending.status == "pending"
        assert new_pending.due_odometer_km == 18000.0

        result = await session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.vehicle_id == "v-3"
            )
        )
        statuses = {row.status for row in result.scalars()}
        assert statuses == {"completed", "pending"}


class TestMaintenanceComplete:

    async def test_complete_is_idempotent(self, session) -> None:
        repo = MaintenanceRepository(session)
        await repo.upsert(
            maintenance_id="v-4:engine_inspection",
            vehicle_id="v-4",
            maintenance_type="engine_inspection",
            priority="high",
            due_odometer_km=10000.0,
        )
        await session.commit()

        first = await repo.complete(
            "v-4:engine_inspection", completed_odometer_km=10000.0
        )
        await session.commit()
        second = await repo.complete(
            "v-4:engine_inspection", completed_odometer_km=9999.0
        )
        await session.commit()

        assert first.completed_at == second.completed_at
        assert first.completed_odometer_km == 10000.0
        assert second.completed_odometer_km == 10000.0

    async def test_complete_defaults_odometer_to_due(self, session) -> None:
        repo = MaintenanceRepository(session)
        await repo.upsert(
            maintenance_id="v-4:fuel_filter_replacement",
            vehicle_id="v-4",
            maintenance_type="fuel_filter_replacement",
            priority="medium",
            due_odometer_km=12000.0,
        )
        await session.commit()

        row = await repo.complete("v-4:fuel_filter_replacement")

        assert row is not None
        assert row.status == "completed"
        assert row.completed_odometer_km == 12000.0
        assert row.completed_at is not None

    async def test_complete_unknown_returns_none(self, session) -> None:
        repo = MaintenanceRepository(session)
        assert await repo.complete("does-not-exist") is None


class TestMaintenanceReconciliation:

    async def test_reconcile_keeps_canonical_row_and_removes_legacy(
        self, session
    ) -> None:
        repo = MaintenanceRepository(session)
        session.add_all(
            [
                MaintenanceRecord(
                    maintenance_id="v-2:oil_change",
                    vehicle_id="v-2",
                    maintenance_type="oil_change",
                    priority="medium",
                    status="pending",
                    due_odometer_km=10000.0,
                    created_at=datetime(
                        2026, 2, 1, 9, 0, tzinfo=timezone.utc
                    ),
                ),
                MaintenanceRecord(
                    maintenance_id="v-2:oil_change:2000",
                    vehicle_id="v-2",
                    maintenance_type="oil_change",
                    priority="medium",
                    status="pending",
                    due_odometer_km=8000.0,
                    created_at=datetime(
                        2026, 2, 2, 9, 0, tzinfo=timezone.utc
                    ),
                ),
                MaintenanceRecord(
                    maintenance_id="v-2:oil_change:4000",
                    vehicle_id="v-2",
                    maintenance_type="oil_change",
                    priority="medium",
                    status="pending",
                    due_odometer_km=6000.0,
                    created_at=datetime(
                        2026, 2, 3, 9, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )
        await session.flush()

        result = await repo.reconcile_duplicates()
        await session.commit()

        assert result["removed"] == 2
        assert result["remaining"] == 3

        pending = await _pending_for(session, "v-2", "oil_change")
        assert [row.maintenance_id for row in pending] == ["v-2:oil_change"]

        result2 = await repo.reconcile_duplicates()
        await session.commit()
        assert result2 == {"removed": 0, "remaining": 3}

    async def test_reconcile_without_canonical_keeps_latest_created(
        self, session
    ) -> None:
        repo = MaintenanceRepository(session)
        session.add_all(
            [
                MaintenanceRecord(
                    maintenance_id="v-2:brake_inspection:1000",
                    vehicle_id="v-2",
                    maintenance_type="brake_inspection",
                    priority="medium",
                    status="pending",
                    due_odometer_km=4000.0,
                    created_at=datetime(
                        2026, 1, 1, 9, 0, tzinfo=timezone.utc
                    ),
                ),
                MaintenanceRecord(
                    maintenance_id="v-2:brake_inspection:2000",
                    vehicle_id="v-2",
                    maintenance_type="brake_inspection",
                    priority="medium",
                    status="pending",
                    due_odometer_km=3000.0,
                    created_at=datetime(
                        2026, 2, 1, 9, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )
        await session.flush()

        await repo.reconcile_duplicates()
        await session.commit()

        pending = await _pending_for(session, "v-2", "brake_inspection")
        assert [row.maintenance_id for row in pending] == [
            "v-2:brake_inspection:2000"
        ]

    async def test_reconcile_leaves_completed_history_alone(
        self, session
    ) -> None:
        repo = MaintenanceRepository(session)
        session.add_all(
            [
                MaintenanceRecord(
                    maintenance_id="v-2:spark_plug_service",
                    vehicle_id="v-2",
                    maintenance_type="spark_plug_service",
                    priority="low",
                    status="completed",
                    due_odometer_km=5000.0,
                    completed_odometer_km=4800.0,
                    created_at=datetime(
                        2026, 1, 1, 9, 0, tzinfo=timezone.utc
                    ),
                    completed_at=datetime(
                        2026, 1, 5, 9, 0, tzinfo=timezone.utc
                    ),
                ),
                MaintenanceRecord(
                    maintenance_id="v-2:spark_plug_service:1000",
                    vehicle_id="v-2",
                    maintenance_type="spark_plug_service",
                    priority="low",
                    status="pending",
                    due_odometer_km=15000.0,
                    created_at=datetime(
                        2026, 3, 1, 9, 0, tzinfo=timezone.utc
                    ),
                ),
            ]
        )
        await session.flush()

        await repo.reconcile_duplicates()
        await session.commit()

        result = await session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.vehicle_id == "v-2",
                MaintenanceRecord.maintenance_type == "spark_plug_service",
            )
        )
        rows = list(result.scalars())
        assert len(rows) == 2
        statuses = {row.status for row in rows}
        assert statuses == {"completed", "pending"}
