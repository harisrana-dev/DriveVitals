import logging

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.assignment import Assignment
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class AssignmentRepository(BaseRepository):
    async def create(
        self,
        assignment_id: str,
        driver_id: str,
        vehicle_id: str,
        route_id: str,
        name: str | None = None,
        notes: str | None = None,
        is_active: bool = True,
    ) -> Assignment:
        assignment = Assignment(
            assignment_id=assignment_id,
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            route_id=route_id,
            name=name,
            notes=notes,
            is_active=is_active,
        )
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get(self, assignment_id: str) -> Assignment | None:
        result = await self._session.execute(
            select(Assignment).where(Assignment.assignment_id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def find_existing(
        self, driver_id: str, vehicle_id: str, route_id: str
    ) -> Assignment | None:
        result = await self._session.execute(
            select(Assignment).where(
                Assignment.driver_id == driver_id,
                Assignment.vehicle_id == vehicle_id,
                Assignment.route_id == route_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        assignment_id: str,
        *,
        driver_id: str | None = None,
        vehicle_id: str | None = None,
        route_id: str | None = None,
        name: str | None = None,
        notes: str | None = None,
        is_active: bool | None = None,
    ) -> Assignment | None:
        assignment = await self.get(assignment_id)
        if assignment is None:
            return None
        values: dict = {}
        if driver_id is not None:
            values["driver_id"] = driver_id
        if vehicle_id is not None:
            values["vehicle_id"] = vehicle_id
        if route_id is not None:
            values["route_id"] = route_id
        if name is not None:
            values["name"] = name
        if notes is not None:
            values["notes"] = notes
        if is_active is not None:
            values["is_active"] = is_active
        if values:
            await self._session.execute(
                update(Assignment)
                .where(Assignment.assignment_id == assignment_id)
                .values(**values)
            )
            await self._session.flush()
        return assignment

    async def delete(self, assignment_id: str) -> bool:
        result = await self._session.execute(
            delete(Assignment).where(Assignment.assignment_id == assignment_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def list(
        self, is_active: bool | None = None
    ) -> list[Assignment]:
        query = select(Assignment)
        if is_active is not None:
            query = query.where(Assignment.is_active == is_active)
        result = await self._session.execute(
            query.order_by(Assignment.created_at)
        )
        return list(result.scalars().all())
