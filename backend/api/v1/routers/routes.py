from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_route_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.route import RouteRead
from backend.api.v1.services.route_service import RouteService

router = APIRouter(prefix="/routes")


@router.get(
    "",
    response_model=PaginatedResponse[RouteRead],
    summary="List routes",
    description="Return a paginated list of routes.",
    tags=["Routes"],
)
async def list_routes(
    limit: int = Query(
        default=100,
        description="Maximum number of routes to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of routes to skip before returning results.",
    ),
    service: RouteService = Depends(get_route_service),
) -> PaginatedResponse[RouteRead]:
    limit, offset = validate_pagination(limit, offset)

    routes, count = await service.list(
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[RouteRead](
        data=[RouteRead.model_validate(route) for route in routes],
        count=count,
    )


@router.get(
    "/{route_id}",
    response_model=Response[RouteRead],
    summary="Get a route",
    description="Return a single route by its id.",
    tags=["Routes"],
)
async def get_route(
    route_id: str,
    service: RouteService = Depends(get_route_service),
) -> Response[RouteRead]:
    route = await service.get(route_id)

    if route is None:
        raise HTTPException(
            status_code=404,
            detail=f"Route {route_id} not found",
        )

    return Response[RouteRead](data=RouteRead.model_validate(route))
