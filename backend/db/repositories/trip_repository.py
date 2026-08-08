import logging
from datetime import datetime

from sqlalchemy import select, update

from backend.db.models.trip import Trip
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TripRepository(BaseRepository):
    async def get_by_id(self, trip_id: str) -> Trip | None:
        result = await self._session.execute(
            select(Trip).where(Trip.trip_id == trip_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        trip_id: str,
        vehicle_id: str,
        driver_id: str,
        route_id: str,
        start_time: datetime,
        status: str = "in_progress",
    ) -> Trip:
        trip = Trip(
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            route_id=route_id,
            start_time=start_time,
            status=status,
        )
        self._session.add(trip)
        await self._session.flush()
        return trip

    async def complete(
        self,
        trip_id: str,
        end_time: datetime,
        distance_km: float,
        duration_seconds: int,
        fuel_used_liters: float,
        average_speed_kmh: float,
        maximum_speed_kmh: float,
        trip_score: float | None = None,
        status: str = "completed",
    ) -> Trip | None:
        result = await self._session.execute(
            select(Trip).where(Trip.trip_id == trip_id)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            logger.warning("Trip %s not found for completion", trip_id)
            return None

        await self._session.execute(
            update(Trip)
            .where(Trip.trip_id == trip_id)
            .values(
                end_time=end_time,
                distance_km=distance_km,
                duration_seconds=duration_seconds,
                fuel_used_liters=fuel_used_liters,
                average_speed_kmh=average_speed_kmh,
                maximum_speed_kmh=maximum_speed_kmh,
                trip_score=trip_score,
                status=status,
            )
        )
        await self._session.flush()
        return existing

    async def abort_stale(self, end_time: datetime) -> int:
        """Mark every ``in_progress`` trip as ``aborted``.

        At runtime startup, ``in_progress`` rows can only belong to a
        previous runtime session (the current session creates its trips
        after this runs). History, recorded metrics and telemetry are
        preserved; only the status and an end/termination timestamp are
        set.
        """
        result = await self._session.execute(
            update(Trip)
            .where(Trip.status == "in_progress")
            .values(
                status="aborted",
                end_time=end_time,
            )
        )
        await self._session.flush()
        return result.rowcount or 0
