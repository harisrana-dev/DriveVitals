from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.system_settings import SystemSettings


class SystemSettingsRepository:
    """Repository for the ``system_settings`` configuration table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, category: str) -> SystemSettings | None:
        result = await self._session.execute(
            select(SystemSettings).where(
                SystemSettings.category == category
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        category: str,
        settings_data: dict,
        updated_by: str | None = None,
    ) -> SystemSettings:
        """Insert or update a configuration category."""
        row = await self.get(category)
        now_kwargs: dict = {}

        if row is None:
            row = SystemSettings(
                category=category,
                settings_data=settings_data,
                updated_by=updated_by,
            )
            self._session.add(row)
        else:
            row.settings_data = settings_data
            if updated_by is not None:
                row.updated_by = updated_by

        await self._session.flush()
        return row
