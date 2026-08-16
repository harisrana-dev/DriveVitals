import logging
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid4, uuid5

from sqlalchemy import delete, select, update

from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

MAINTENANCE_ID_MAX_LENGTH = 36


class MaintenanceRepository(BaseRepository):

    async def insert(
        self,
        maintenance_id: str,
        vehicle_id: str,
        maintenance_type: str,
        priority: str,
        status: str = "pending",
        due_odometer_km: float | None = None,
        due_date: datetime | None = None,
        component: str | None = None,
        reason: str | None = None,
        recommended_action: str | None = None,
        estimated_cost: float | None = None,
        completed_odometer_km: float | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> MaintenanceRecord:
        record = MaintenanceRecord(
            maintenance_id=maintenance_id,
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            priority=priority,
            status=status,
            due_odometer_km=due_odometer_km,
            due_date=due_date,
            component=component,
            reason=reason,
            recommended_action=recommended_action,
            estimated_cost=estimated_cost,
            completed_odometer_km=completed_odometer_km,
            created_at=created_at or datetime.now(timezone.utc),
            completed_at=completed_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def upsert(
        self,
        maintenance_id: str,
        vehicle_id: str,
        maintenance_type: str,
        priority: str,
        status: str = "pending",
        due_odometer_km: float | None = None,
        due_date: datetime | None = None,
        component: str | None = None,
        reason: str | None = None,
        recommended_action: str | None = None,
        estimated_cost: float | None = None,
        completed_odometer_km: float | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> MaintenanceRecord:
        """Idempotently persist the current pending work item for a vehicle.

        The runtime generates records keyed by a stable identity
        (``{vehicle_id}:{maintenance_type}``). To stay correct across the
        completed/uncompleted boundary:

        1. An existing *pending* row for the same (vehicle_id, type) is
           updated in place, no matter which identity variant created it
           (canonical form or a legacy projection). This is what keeps the
           81 legacy duplicates from being recreated on the next cycle.
        2. Otherwise a new pending row is inserted. If the requested
           identity is already taken by a *completed* row, a fresh identity
           is minted so completed history survives as history.

        ``created_at`` is only ever set on insert; updates leave the original
        date alone so it stays the real creation time of the work item.
        """
        existing = await self._find_pending(vehicle_id, maintenance_type)
        if existing is not None:
            await self._session.execute(
                update(MaintenanceRecord)
                .where(MaintenanceRecord.maintenance_id == existing.maintenance_id)
                .values(
                    maintenance_type=maintenance_type,
                    priority=priority,
                    status=status,
                    due_odometer_km=due_odometer_km,
                    due_date=due_date,
                    component=component,
                    reason=reason,
                    recommended_action=recommended_action,
                    estimated_cost=estimated_cost,
                    completed_odometer_km=completed_odometer_km,
                    completed_at=completed_at,
                )
            )
            await self._session.flush()
            return existing

        stored_id = self._scope_maintenance_id(maintenance_id)
        if await self._get(stored_id) is not None:
            stored_id = self._scope_maintenance_id(
                f"{stored_id}:{uuid4().hex[:8]}"
            )
        record = MaintenanceRecord(
            maintenance_id=stored_id,
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            priority=priority,
            status=status,
            due_odometer_km=due_odometer_km,
            due_date=due_date,
            component=component,
            reason=reason,
            recommended_action=recommended_action,
            estimated_cost=estimated_cost,
            completed_odometer_km=completed_odometer_km,
            created_at=created_at or datetime.now(timezone.utc),
            completed_at=completed_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get(
        self,
        maintenance_id: str,
    ) -> MaintenanceRecord | None:
        return await self._get(maintenance_id)

    async def complete(
        self,
        maintenance_id: str,
        completed_odometer_km: float | None = None,
    ) -> MaintenanceRecord | None:
        """Mark a pending record completed. Idempotent: completing an
        already-completed record returns it unchanged."""
        row = await self._get(maintenance_id)
        if row is None:
            return None
        if row.status == "completed":
            return row
        row.status = "completed"
        row.completed_at = datetime.now(timezone.utc)
        row.completed_odometer_km = (
            completed_odometer_km
            if completed_odometer_km is not None
            else row.due_odometer_km
        )
        await self._session.flush()
        return row

    async def reconcile_duplicates(self) -> dict[str, int]:
        """Consolidate legacy duplicate *pending* projections.

        Keeps a single pending row per (vehicle_id, maintenance_type):
        the canonical ``{vehicle_id}:{maintenance_type}`` identity when it
        exists, otherwise the row with the latest ``created_at`` (falling
        back to the lexicographically largest id for determinism). Every
        other pending row in the group is deleted.

        Idempotent: on an already-consolidated table a second invocation
        removes nothing.
        """
        result = await self._session.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.status == "pending"
            )
        )
        rows = list(result.scalars().all())

        groups: dict[tuple[str, str], list[MaintenanceRecord]] = {}
        for row in rows:
            groups.setdefault(
                (row.vehicle_id, row.maintenance_type), []
            ).append(row)

        to_delete: list[str] = []
        remaining = 0
        for group in groups.values():
            if len(group) == 1:
                remaining += 1
                continue
            canonical = [
                row
                for row in group
                if row.maintenance_id
                == f"{row.vehicle_id}:{row.maintenance_type}"
            ]
            if canonical:
                keeper_id = canonical[0].maintenance_id
            else:
                keeper = max(
                    group,
                    key=lambda row: (
                        row.created_at
                        or datetime.min.replace(tzinfo=timezone.utc),
                        row.maintenance_id,
                    ),
                )
                keeper_id = keeper.maintenance_id
            for row in group:
                if row.maintenance_id != keeper_id:
                    to_delete.append(row.maintenance_id)
            remaining += 1

        if to_delete:
            await self._session.execute(
                delete(MaintenanceRecord).where(
                    MaintenanceRecord.maintenance_id.in_(to_delete)
                )
            )
            await self._session.flush()
        return {"removed": len(to_delete), "remaining": remaining}

    async def _get(
        self,
        maintenance_id: str,
    ) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.maintenance_id == maintenance_id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _find_pending(
        self,
        vehicle_id: str,
        maintenance_type: str,
    ) -> MaintenanceRecord | None:
        result = await self._session.execute(
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.vehicle_id == vehicle_id,
                MaintenanceRecord.maintenance_type == maintenance_type,
                MaintenanceRecord.status == "pending",
            )
            .order_by(MaintenanceRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _scope_maintenance_id(deterministic: str) -> str:
        if len(deterministic) > MAINTENANCE_ID_MAX_LENGTH:
            return str(uuid5(NAMESPACE_OID, deterministic))
        return deterministic
