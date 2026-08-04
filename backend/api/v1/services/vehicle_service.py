from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.trip import Trip
from backend.db.models.vehicle import Vehicle
from backend.db.repositories.vehicle_repository import VehicleRepository

from backend.api.v1.services import paginate


class VehicleService:

    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        status: str | None,
        driver: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Vehicle], int]:
        query = select(Vehicle)

        if status is not None:
            query = query.where(Vehicle.status == status)

        if driver is not None:
            query = query.where(
                Vehicle.vehicle_id.in_(
                    select(Trip.vehicle_id).where(Trip.driver_id == driver)
                )
            )

        query = query.order_by(Vehicle.vehicle_id)

        return await paginate(self._session, query, limit, offset)

    async def get(self, vehicle_id: str) -> Vehicle | None:
        result = await self._session.execute(
            select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
        )
        return result.scalar_one_or_none()
