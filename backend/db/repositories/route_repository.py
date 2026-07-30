import logging

from sqlalchemy import select, update

from backend.db.models.route import Route
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RouteRepository(BaseRepository):
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
