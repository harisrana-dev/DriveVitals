from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.repositories.maintenance_repository import (
    MaintenanceRepository,
)

from backend.api.v1.services import paginate

PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

VALID_SORTS = ("created_at", "priority", "due_odometer_km", "due_date")


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
        status: str | None,
        sort: str | None,
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

        if status is not None:
            query = query.where(
                MaintenanceRecord.status == status
            )

        if sort == "due_odometer_km":
            query = query.order_by(
                MaintenanceRecord.due_odometer_km.asc().nulls_last()
            )
        elif sort == "due_date":
            query = query.order_by(
                MaintenanceRecord.due_date.asc().nulls_last()
            )
        elif sort == "priority":
            query = query.order_by(
                case(
                    *[
                        (
                            MaintenanceRecord.priority == value,
                            rank,
                        )
                        for value, rank in PRIORITY_ORDER.items()
                    ],
                    else_=99,
                ).asc()
            )
        else:
            query = query.order_by(MaintenanceRecord.created_at.desc())

        return await paginate(self._session, query, limit, offset)

    async def complete(
        self,
        maintenance_id: str,
        completed_odometer_km: float | None,
    ) -> MaintenanceRecord | None:
        record = await self._repository.complete(
            maintenance_id=maintenance_id,
            completed_odometer_km=completed_odometer_km,
        )
        if record is not None:
            await self._session.commit()
        return record
