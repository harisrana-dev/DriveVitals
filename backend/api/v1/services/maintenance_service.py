from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.repositories.maintenance_repository import (
    MaintenanceRepository,
)

from backend.api.v1.services import paginate


class MaintenanceService:

    def __init__(self, repository: MaintenanceRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        vehicle_id: str | None,
        priority: str | None,
        component: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[MaintenanceRecord], int]:
        query = select(MaintenanceRecord)

        if vehicle_id is not None:
            query = query.where(
                MaintenanceRecord.vehicle_id == vehicle_id
            )

        if priority is not None:
            query = query.where(
                MaintenanceRecord.priority == priority
            )

        if component is not None:
            query = query.where(
                MaintenanceRecord.maintenance_type == component
            )

        query = query.order_by(MaintenanceRecord.created_at.desc())

        return await paginate(self._session, query, limit, offset)
