import logging

from sqlalchemy import delete, func, select, update

from backend.db.models.vehicle import Vehicle
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class VehicleRepository(BaseRepository):
    async def get(self, vehicle_id: str) -> Vehicle | None:
        result = await self._session.execute(
            select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int, offset: int) -> tuple[list[Vehicle], int]:
        query = select(Vehicle).order_by(Vehicle.created_at)
        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        result = await self._session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def create(
        self,
        vehicle_id: str,
        manufacturer: str,
        model: str,
        year: int,
        *,
        registration_number: str | None = None,
        vin: str | None = None,
        fuel_type: str = "gasoline",
        status: str = "active",
        display_name: str | None = None,
        fuel_efficiency_factor: float = 1.0,
        acceleration_response: float = 1.0,
        tank_capacity_liters: float = 60.0,
    ) -> Vehicle:
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            registration_number=registration_number or f"REG-{vehicle_id}",
            vin=vin or f"VIN-{vehicle_id}",
            manufacturer=manufacturer,
            model=model,
            year=year,
            fuel_type=fuel_type,
            status=status,
            display_name=display_name,
            fuel_efficiency_factor=fuel_efficiency_factor,
            acceleration_response=acceleration_response,
            tank_capacity_liters=tank_capacity_liters,
        )
        self._session.add(vehicle)
        await self._session.flush()
        return vehicle

    async def update(self, vehicle_id: str, **values: object) -> Vehicle | None:
        vehicle = await self.get(vehicle_id)
        if vehicle is None:
            return None
        clean = {
            k: v
            for k, v in values.items()
            if v is not None and hasattr(Vehicle, k) and k != "vehicle_id"
        }
        if clean:
            await self._session.execute(
                update(Vehicle)
                .where(Vehicle.vehicle_id == vehicle_id)
                .values(**clean)
            )
            await self._session.flush()
        return vehicle

    async def delete(self, vehicle_id: str) -> bool:
        result = await self._session.execute(
            delete(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
        )
        await self._session.flush()
        return result.rowcount > 0

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
