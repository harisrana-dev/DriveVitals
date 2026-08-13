import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from backend.db.models.driver_statistics import DriverStatistics
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DriverStatisticsRepository(BaseRepository):
    async def upsert(
        self,
        driver_id: str,
        safety_score: float | None = None,
        aggression_score: float | None = None,
        efficiency_score: float | None = None,
        speeding_events: int | None = None,
        harsh_braking_events: int | None = None,
        aggressive_throttle_events: int | None = None,
        high_rpm_events: int | None = None,
        total_distance_km: float | None = None,
        total_trips: int | None = None,
        total_driving_time_seconds: int | None = None,
        average_trip_score: float | None = None,
        fuel_efficiency: float | None = None,
        last_updated: datetime | None = None,
    ) -> DriverStatistics:
        result = await self._session.execute(
            select(DriverStatistics).where(
                DriverStatistics.driver_id == driver_id
            )
        )
        existing = result.scalar_one_or_none()

        now = last_updated or datetime.now(timezone.utc)

        if existing is not None:
            updates: dict[str, object] = {"last_updated": now}
            if safety_score is not None:
                updates["safety_score"] = safety_score
            if aggression_score is not None:
                updates["aggression_score"] = aggression_score
            if efficiency_score is not None:
                updates["efficiency_score"] = efficiency_score
            if speeding_events is not None:
                updates["speeding_events"] = speeding_events
            if harsh_braking_events is not None:
                updates["harsh_braking_events"] = harsh_braking_events
            if aggressive_throttle_events is not None:
                updates["aggressive_throttle_events"] = (
                    aggressive_throttle_events
                )
            if high_rpm_events is not None:
                updates["high_rpm_events"] = high_rpm_events
            if total_distance_km is not None:
                updates["total_distance_km"] = total_distance_km
            if total_trips is not None:
                updates["total_trips"] = total_trips
            if total_driving_time_seconds is not None:
                updates["total_driving_time_seconds"] = (
                    total_driving_time_seconds
                )
            if average_trip_score is not None:
                updates["average_trip_score"] = average_trip_score
            if fuel_efficiency is not None:
                updates["fuel_efficiency"] = fuel_efficiency
            await self._session.execute(
                update(DriverStatistics)
                .where(DriverStatistics.driver_id == driver_id)
                .values(**updates)
            )
            await self._session.flush()
            return existing

        statistics = DriverStatistics(
            driver_id=driver_id,
            safety_score=safety_score if safety_score is not None else 0.0,
            aggression_score=(
                aggression_score if aggression_score is not None else 0.0
            ),
            efficiency_score=(
                efficiency_score if efficiency_score is not None else 0.0
            ),
            total_trips=total_trips if total_trips is not None else 0,
            total_distance_km=(
                total_distance_km if total_distance_km is not None else 0.0
            ),
            speeding_events=(
                speeding_events if speeding_events is not None else 0
            ),
            harsh_braking_events=(
                harsh_braking_events
                if harsh_braking_events is not None
                else 0
            ),
            aggressive_throttle_events=(
                aggressive_throttle_events
                if aggressive_throttle_events is not None
                else 0
            ),
            high_rpm_events=(
                high_rpm_events if high_rpm_events is not None else 0
            ),
            total_driving_time_seconds=(
                total_driving_time_seconds
                if total_driving_time_seconds is not None
                else 0
            ),
            average_trip_score=(
                average_trip_score
                if average_trip_score is not None
                else 0.0
            ),
            fuel_efficiency=(
                fuel_efficiency if fuel_efficiency is not None else 0.0
            ),
            last_updated=now,
        )
        self._session.add(statistics)
        await self._session.flush()
        return statistics

    async def get_by_driver(self, driver_id: str) -> DriverStatistics | None:
        result = await self._session.execute(
            select(DriverStatistics).where(
                DriverStatistics.driver_id == driver_id
            )
        )
        return result.scalar_one_or_none()
