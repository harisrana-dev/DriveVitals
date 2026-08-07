from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.telemetry_sample import TelemetrySample
from backend.db.repositories.telemetry_repository import TelemetryRepository

from backend.api.v1.services import paginate


class TelemetryService:

    def __init__(self, repository: TelemetryRepository) -> None:
        self._repository = repository

    @property
    def _session(self) -> AsyncSession:
        return self._repository._session

    async def list(
        self,
        vehicle_id: str | None,
        trip_id: str | None,
        latest: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[TelemetrySample], int]:
        if latest and vehicle_id is not None:
            query = (
                select(TelemetrySample)
                .where(TelemetrySample.vehicle_id == vehicle_id)
                .order_by(TelemetrySample.timestamp.desc())
            )
            result = await self._session.execute(query.limit(1))
            rows = list(result.scalars().all())
            return rows, len(rows)

        query = select(TelemetrySample)

        if vehicle_id is not None:
            query = query.where(TelemetrySample.vehicle_id == vehicle_id)

        if trip_id is not None:
            query = query.where(TelemetrySample.trip_id == trip_id)

        if latest:
            query = query.distinct(TelemetrySample.vehicle_id).order_by(
                TelemetrySample.vehicle_id,
                TelemetrySample.timestamp.desc(),
            )
        else:
            query = query.order_by(TelemetrySample.timestamp.desc())

        return await paginate(self._session, query, limit, offset)
