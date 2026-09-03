import logging

from sqlalchemy import delete, func, select, update

from backend.db.models.route import Route
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RouteRepository(BaseRepository):
    async def get(self, route_id: str) -> Route | None:
        result = await self._session.execute(
            select(Route).where(Route.route_id == route_id)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int, offset: int) -> tuple[list[Route], int]:
        query = select(Route).order_by(Route.created_at)
        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        result = await self._session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def create(
        self,
        route_id: str,
        name: str,
        route_type: str,
        origin: str,
        destination: str,
        estimated_distance_km: float,
        *,
        speed_limit_kmh: float = 60.0,
        is_active: bool = True,
    ) -> Route:
        route = Route(
            route_id=route_id,
            name=name,
            route_type=route_type,
            origin=origin,
            destination=destination,
            estimated_distance_km=estimated_distance_km,
            speed_limit_kmh=speed_limit_kmh,
            is_active=is_active,
        )
        self._session.add(route)
        await self._session.flush()
        return route

    async def update(self, route_id: str, **values: object) -> Route | None:
        route = await self.get(route_id)
        if route is None:
            return None
        clean = {
            k: v
            for k, v in values.items()
            if v is not None and hasattr(Route, k) and k != "route_id"
        }
        if clean:
            await self._session.execute(
                update(Route)
                .where(Route.route_id == route_id)
                .values(**clean)
            )
            await self._session.flush()
        return route

    async def delete(self, route_id: str) -> bool:
        result = await self._session.execute(
            delete(Route).where(Route.route_id == route_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def upsert(self, route_id: str, name: str, route_type: str, origin: str, destination: str, estimated_distance_km: float) -> Route:
        result = await self._session.execute(
            select(Route).where(Route.route_id == route_id)
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            updates: dict[str, object] = {}
            if name is not None and name != existing.name:
                updates["name"] = name
            if route_type is not None and route_type != existing.route_type:
                updates["route_type"] = route_type
            if origin is not None and origin != existing.origin:
                updates["origin"] = origin
            if destination is not None and destination != existing.destination:
                updates["destination"] = destination
            if estimated_distance_km is not None and estimated_distance_km != existing.estimated_distance_km:
                updates["estimated_distance_km"] = estimated_distance_km
            if updates:
                await self._session.execute(
                    update(Route)
                    .where(Route.route_id == route_id)
                    .values(**updates)
                )
                await self._session.flush()
            return existing

        route = Route(
            route_id=route_id,
            name=name,
            route_type=route_type,
            origin=origin,
            destination=destination,
            estimated_distance_km=estimated_distance_km,
        )
        self._session.add(route)
        await self._session.flush()
        return route
