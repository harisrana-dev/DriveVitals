from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.alert import Alert
from backend.db.repositories.alert_repository import AlertRepository

from backend.api.v1.services import paginate


class AlertService:

    def __init__(self, repository: AlertRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        vehicle_id: str | None,
        severity: str | None,
        alert_type: str | None,
        acknowledged: bool | None,
        status: str | None,
        category: str | None,
        driver_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Alert], int]:
        query = select(Alert)

        if vehicle_id is not None:
            query = query.where(Alert.vehicle_id == vehicle_id)

        if severity is not None:
            query = query.where(Alert.severity == severity)

        if alert_type is not None:
            query = query.where(Alert.alert_type == alert_type)

        if acknowledged is not None:
            query = query.where(Alert.acknowledged == acknowledged)

        if status is not None:
            query = query.where(Alert.status == status)

        if category is not None:
            query = query.where(Alert.category == category)

        if driver_id is not None:
            query = query.where(Alert.driver_id == driver_id)

        if start_time is not None:
            query = query.where(Alert.created_at >= start_time)

        if end_time is not None:
            query = query.where(Alert.created_at <= end_time)

        query = query.order_by(Alert.created_at.desc())

        return await paginate(self._session, query, limit, offset)

    async def stats(
        self,
        vehicle_id: str | None = None,
        severity: str | None = None,
        alert_type: str | None = None,
        acknowledged: bool | None = None,
        status: str | None = None,
        category: str | None = None,
        driver_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict:
        """Return aggregate statistics for alerts matching the filters."""
        query = select(
            func.count(Alert.alert_id),
            func.count().filter(Alert.severity == "critical").label("critical_count"),
            func.count().filter(Alert.severity == "high").label("high_count"),
            func.count().filter(Alert.status == "active").label("active_count"),
            func.count().filter(Alert.acknowledged == True).label("acknowledged_count"),
            func.count().filter(Alert.status == "resolved").label("resolved_count"),
        )

        if vehicle_id is not None:
            query = query.where(Alert.vehicle_id == vehicle_id)

        if severity is not None:
            query = query.where(Alert.severity == severity)

        if alert_type is not None:
            query = query.where(Alert.alert_type == alert_type)

        if acknowledged is not None:
            query = query.where(Alert.acknowledged == acknowledged)

        if status is not None:
            query = query.where(Alert.status == status)

        if category is not None:
            query = query.where(Alert.category == category)

        if driver_id is not None:
            query = query.where(Alert.driver_id == driver_id)

        if start_time is not None:
            query = query.where(Alert.created_at >= start_time)

        if end_time is not None:
            query = query.where(Alert.created_at <= end_time)

        result = await self._session.execute(query)
        row = result.one()

        return {
            "total": row[0] or 0,
            "critical_active": row[1] or 0,
            "high_active": row[2] or 0,
            "active": row[3] or 0,
            "acknowledged": row[4] or 0,
            "resolved": row[5] or 0,
        }

    async def acknowledge(self, alert_id: str) -> Alert | None:
        alert = await self._repository.acknowledge(alert_id)
        if alert is not None:
            await self._session.commit()
        return alert

    async def resolve(self, alert_id: str) -> Alert | None:
        alert = await self._repository.resolve(alert_id)
        if alert is not None:
            await self._session.commit()
        return alert
