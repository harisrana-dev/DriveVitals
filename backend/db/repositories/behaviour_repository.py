import logging
from datetime import datetime

from sqlalchemy import select

from backend.db.models.behaviour_event import BehaviourEvent
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class BehaviourRepository(BaseRepository):
    async def insert(
        self,
        trip_id: str,
        vehicle_id: str,
        driver_id: str,
        event_type: str,
        severity: str,
        started_at: datetime,
        ended_at: datetime,
        duration_seconds: float,
        distance_km: float,
        maximum_value: float,
        average_value: float,
    ) -> BehaviourEvent:
        event = BehaviourEvent(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            event_type=event_type,
            severity=severity,
            started_at=started_at,
            ended_at=ended_at,
            duration_seconds=duration_seconds,
            distance_km=distance_km,
            maximum_value=maximum_value,
            average_value=average_value,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_by_trip_ids(
        self,
        trip_ids: list[str],
    ) -> list[BehaviourEvent]:
        """Return behaviour events belonging to the given trip ids."""
        if not trip_ids:
            return []
        result = await self._session.execute(
            select(BehaviourEvent).where(
                BehaviourEvent.trip_id.in_(trip_ids)
            )
        )
        return list(result.scalars().all())
