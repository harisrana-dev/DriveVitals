from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.trip import Trip
from backend.db.repositories.trip_repository import TripRepository

from backend.api.v1.services import paginate


class TripService:

    def __init__(self, repository: TripRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        vehicle_id: str | None,
        driver_id: str | None,
        completed: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Trip], int]:
        query = select(Trip)

        if vehicle_id is not None:
            query = query.where(Trip.vehicle_id == vehicle_id)

        if driver_id is not None:
            query = query.where(Trip.driver_id == driver_id)

        if completed is True:
            query = query.where(Trip.status == "completed")
        elif completed is False:
            query = query.where(Trip.status != "completed")

        query = query.order_by(Trip.start_time.desc())

        return await paginate(self._session, query, limit, offset)

    async def get(self, trip_id: str) -> Trip | None:
        return await self._repository.get_by_id(trip_id)
