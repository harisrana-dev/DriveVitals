from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.route import Route
from backend.db.repositories.route_repository import RouteRepository

from backend.api.v1.services import paginate


class RouteService:

    def __init__(self, repository: RouteRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        limit: int,
        offset: int,
    ) -> tuple[list[Route], int]:
        query = select(Route).order_by(Route.route_id)

        return await paginate(self._session, query, limit, offset)

    async def get(self, route_id: str) -> Route | None:
        result = await self._session.execute(
            select(Route).where(Route.route_id == route_id)
        )
        return result.scalar_one_or_none()
