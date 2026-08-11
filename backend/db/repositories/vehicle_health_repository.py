import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

from backend.db.models.vehicle_health import VehicleHealth
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class VehicleHealthRepository(BaseRepository):
    async def upsert(
        self,
        vehicle_id: str,
        overall_health_score: float | None = None,
        engine_health: float | None = None,
        brake_health: float | None = None,
        transmission_health: float | None = None,
        cooling_health: float | None = None,
        fuel_system_health: float | None = None,
        last_updated: datetime | None = None,
    ) -> VehicleHealth:
        result = await self._session.execute(
            select(VehicleHealth).where(VehicleHealth.vehicle_id == vehicle_id)
        )
        existing = result.scalar_one_or_none()

        now = last_updated or datetime.now(timezone.utc)

        if existing is not None:
            updates: dict[str, object] = {"last_updated": now}
            if overall_health_score is not None:
                updates["overall_health_score"] = overall_health_score
            if engine_health is not None:
                updates["engine_health"] = engine_health
            if brake_health is not None:
                updates["brake_health"] = brake_health
            if transmission_health is not None:
                updates["transmission_health"] = transmission_health
            if cooling_health is not None:
                updates["cooling_health"] = cooling_health
            if fuel_system_health is not None:
                updates["fuel_system_health"] = fuel_system_health
            await self._session.execute(
                update(VehicleHealth)
                .where(VehicleHealth.vehicle_id == vehicle_id)
                .values(**updates)
            )
            await self._session.flush()
            return existing

        health = VehicleHealth(
            vehicle_id=vehicle_id,
            overall_health_score=overall_health_score,
            engine_health=engine_health,
            brake_health=brake_health,
            transmission_health=transmission_health,
            cooling_health=cooling_health,
            fuel_system_health=fuel_system_health,
            last_updated=now,
        )
        self._session.add(health)
        await self._session.flush()
        return health
