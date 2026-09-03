import logging

from sqlalchemy import delete, func, select, update

from backend.db.models.driver import Driver
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DriverRepository(BaseRepository):
    async def get(self, driver_id: str) -> Driver | None:
        result = await self._session.execute(
            select(Driver).where(Driver.driver_id == driver_id)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int, offset: int) -> tuple[list[Driver], int]:
        query = select(Driver).order_by(Driver.created_at)
        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        result = await self._session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def create(
        self,
        driver_id: str,
        first_name: str,
        last_name: str,
        *,
        license_number: str | None = None,
        employment_status: str = "active",
        behavior_profile: str = "standard",
    ) -> Driver:
        driver = Driver(
            driver_id=driver_id,
            first_name=first_name,
            last_name=last_name,
            license_number=license_number or f"LIC-{driver_id}",
            employment_status=employment_status,
            behavior_profile=behavior_profile,
        )
        self._session.add(driver)
        await self._session.flush()
        return driver

    async def update(
        self,
        driver_id: str,
        **values: object,
    ) -> Driver | None:
        driver = await self.get(driver_id)
        if driver is None:
            return None
        updates = {k: v for k, v in values.items() if v is not None}
        if updates:
            clean = {
                k: v
                for k, v in updates.items()
                if hasattr(Driver, k) and k not in ("driver_id",)
            }
            if clean:
                await self._session.execute(
                    update(Driver)
                    .where(Driver.driver_id == driver_id)
                    .values(**clean)
                )
                await self._session.flush()
        return driver

    async def delete(self, driver_id: str) -> bool:
        result = await self._session.execute(
            delete(Driver).where(Driver.driver_id == driver_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def upsert(self, driver_id: str, first_name: str, last_name: str, **kwargs: object) -> Driver:
        result = await self._session.execute(
            select(Driver).where(Driver.driver_id == driver_id)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            updates: dict[str, object] = {}
            if first_name is not None and first_name != existing.first_name:
                updates["first_name"] = first_name
            if last_name is not None and last_name != existing.last_name:
                updates["last_name"] = last_name
            for key, value in kwargs.items():
                if value is not None and hasattr(existing, key) and getattr(existing, key) != value:
                    updates[key] = value
            if updates:
                await self._session.execute(
                    update(Driver)
                    .where(Driver.driver_id == driver_id)
                    .values(**updates)
                )
                await self._session.flush()
            return existing

        driver = Driver(
            driver_id=driver_id,
            first_name=first_name,
            last_name=last_name,
            license_number=kwargs.get("license_number", f"LIC-{driver_id}"),
            employment_status=kwargs.get("employment_status", "active"),
        )
        self._session.add(driver)
        await self._session.flush()
        return driver
