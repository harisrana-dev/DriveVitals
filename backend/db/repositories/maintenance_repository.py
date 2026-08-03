import logging
from datetime import datetime, timezone

from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


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
