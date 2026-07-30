import logging

from sqlalchemy import select, update

from backend.db.models.driver import Driver
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DriverRepository(BaseRepository):
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
