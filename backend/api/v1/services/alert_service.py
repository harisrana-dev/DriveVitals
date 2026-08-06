from sqlalchemy import select
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

        query = query.order_by(Alert.created_at.desc())

        return await paginate(self._session, query, limit, offset)

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
