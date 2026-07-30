import logging

from sqlalchemy import select, update

from backend.db.models.vehicle import Vehicle
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class VehicleRepository(BaseRepository):
    async def upsert(self, vehicle_id: str, manufacturer: str, model: str, year: int, **kwargs: object) -> Vehicle:
        result = await self._session.execute(
            select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            updates: dict[str, object] = {}
            if manufacturer is not None and manufacturer != existing.manufacturer:
                updates["manufacturer"] = manufacturer
            if model is not None and model != existing.model:
                updates["model"] = model
            if year is not None and year != existing.year:
                updates["year"] = year
            for key, value in kwargs.items():
                if value is not None and hasattr(existing, key) and getattr(existing, key) != value:
                    updates[key] = value
            if updates:
                await self._session.execute(
                    update(Vehicle)
                    .where(Vehicle.vehicle_id == vehicle_id)
                    .values(**updates)
                )
                await self._session.flush()
            return existing

        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            registration_number=kwargs.get("registration_number", f"REG-{vehicle_id}"),
            vin=kwargs.get("vin", f"VIN-{vehicle_id}"),
            manufacturer=manufacturer,
            model=model,
            year=year,
            fuel_type=kwargs.get("fuel_type", "gasoline"),
            status=kwargs.get("status", "active"),
        )
        self._session.add(vehicle)
        await self._session.flush()
        return vehicle
