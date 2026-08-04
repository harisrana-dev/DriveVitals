from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.driver import Driver
from backend.db.repositories.driver_repository import DriverRepository

from backend.api.v1.services import paginate


class DriverService:

    def __init__(self, repository: DriverRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[Driver], int]:
        query = select(Driver).order_by(Driver.driver_id)

        return await paginate(self._session, query, limit, offset)

    async def get(self, driver_id: str) -> Driver | None:
        result = await self._session.execute(
            select(Driver).where(Driver.driver_id == driver_id)
        )
        return result.scalar_one_or_none()
