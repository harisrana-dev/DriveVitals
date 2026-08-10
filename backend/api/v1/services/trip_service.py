from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.route import Route
from backend.db.models.trip import Trip
from backend.db.repositories.trip_repository import TripRepository

from backend.api.v1.services import paginate


class TripService:

    def __init__(self, repository: TripRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    @staticmethod
    def _loads() -> list:
        return [
            selectinload(Trip.route),
            selectinload(Trip.vehicle),
            selectinload(Trip.driver),
            selectinload(Trip.behaviour_events),
        ]

    async def list(
        self,
        vehicle_id: str | None,
        driver_id: str | None,
        completed: bool | None,
        statuses: list[str] | None,
        route_type: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Trip], int]:
        query = select(Trip).options(*self._loads())

        if vehicle_id is not None:
            query = query.where(Trip.vehicle_id == vehicle_id)

        if driver_id is not None:
            query = query.where(Trip.driver_id == driver_id)

        if statuses:
            query = query.where(Trip.status.in_(statuses))
        elif completed is True:
            query = query.where(Trip.status == "completed")
        elif completed is False:
            query = query.where(Trip.status != "completed")

        if route_type:
            query = query.join(Trip.route).where(Route.route_type == route_type)

        query = query.order_by(Trip.start_time.desc(), Trip.trip_id.desc())

        return await paginate(self._session, query, limit, offset)

    async def get(self, trip_id: str) -> Trip | None:
        query = (
            select(Trip)
            .options(*self._loads())
            .where(Trip.trip_id == trip_id)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()