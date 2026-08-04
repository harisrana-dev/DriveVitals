from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.driver_statistics import DriverStatistics
from backend.db.repositories.driver_statistics_repository import (
    DriverStatisticsRepository,
)

from backend.api.v1.services import paginate


class DriverStatisticsService:

    def __init__(self, repository: DriverStatisticsRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[DriverStatistics], int]:
        query = select(DriverStatistics).order_by(
            DriverStatistics.driver_id
        )

        return await paginate(self._session, query, limit, offset)

    async def get(self, driver_id: str) -> DriverStatistics | None:
        return await self._repository.get_by_driver(driver_id)
