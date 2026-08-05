import logging
from datetime import datetime, timezone
from uuid import NAMESPACE_OID, uuid5

from sqlalchemy import select, update

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
        completed_odometer_km: float | None = None,
        created_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> MaintenanceRecord:
        """Idempotently persist one maintenance record keyed by a stable identity.

        The stored maintenance_id stays deterministic (the generator's own
        ``{vehicle_id}:{maintenance_type}:{projected_odometer}`` form, hashed
        only when it exceeds the 36-character column), so replaying the same
        record set across runtime cycles resolves to the same row instead of
        violating the maintenance_records primary key.

        - An existing record is updated in place with its mutable fields.
        - A genuinely new record is inserted.
        """
        created_at = created_at or datetime.now(timezone.utc)
        stored_id = self._scope_maintenance_id(maintenance_id)

        existing = await self._session.execute(
            select(MaintenanceRecord)
            .where(MaintenanceRecord.maintenance_id == stored_id)
            .limit(1)
        )
        existing_row = existing.scalar_one_or_none()

        if existing_row is not None:
            await self._session.execute(
                update(MaintenanceRecord)
                .where(MaintenanceRecord.maintenance_id == stored_id)
                .values(
                    maintenance_type=maintenance_type,
                    priority=priority,
                    status=status,
                    due_odometer_km=due_odometer_km,
                    completed_odometer_km=completed_odometer_km,
                    created_at=created_at,
                    completed_at=completed_at,
                )
            )
            await self._session.flush()
            return existing_row

        record = MaintenanceRecord(
            maintenance_id=stored_id,
            vehicle_id=vehicle_id,
            maintenance_type=maintenance_type,
            priority=priority,
            status=status,
            due_odometer_km=due_odometer_km,
            completed_odometer_km=completed_odometer_km,
            created_at=created_at,
            completed_at=completed_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    @staticmethod
    def _scope_maintenance_id(deterministic: str) -> str:
        if len(deterministic) > MAINTENANCE_ID_MAX_LENGTH:
            return str(uuid5(NAMESPACE_OID, deterministic))
        return deterministic
