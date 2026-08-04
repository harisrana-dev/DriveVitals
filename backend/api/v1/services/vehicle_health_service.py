from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.vehicle_health import VehicleHealth
from backend.db.repositories.vehicle_health_repository import (
    VehicleHealthRepository,
)

from backend.api.v1.services import paginate


class VehicleHealthService:

    def __init__(self, repository: VehicleHealthRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[VehicleHealth], int]:
        query = select(VehicleHealth).order_by(VehicleHealth.vehicle_id)

        return await paginate(self._session, query, limit, offset)

    async def get(self, vehicle_id: str) -> VehicleHealth | None:
        result = await self._session.execute(
            select(VehicleHealth).where(VehicleHealth.vehicle_id == vehicle_id)
        )
        return result.scalar_one_or_none()
