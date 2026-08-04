from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_driver_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.driver import DriverRead
from backend.api.v1.services.driver_service import DriverService

router = APIRouter(prefix="/drivers")


@router.get(
    "",
    response_model=PaginatedResponse[DriverRead],
    summary="List drivers",
    description="Return a paginated list of drivers.",
    tags=["Drivers"],
)
async def list_drivers(
    limit: int = Query(
        default=100,
        description="Maximum number of drivers to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of drivers to skip before returning results.",
    ),
    service: DriverService = Depends(get_driver_service),
) -> PaginatedResponse[DriverRead]:
    limit, offset = validate_pagination(limit, offset)

    drivers, count = await service.list(
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[DriverRead](
        data=[DriverRead.model_validate(driver) for driver in drivers],
        count=count,
    )


@router.get(
    "/{driver_id}",
    response_model=Response[DriverRead],
    summary="Get a driver",
    description="Return a single driver by its id.",
    tags=["Drivers"],
)
async def get_driver(
    driver_id: str,
    service: DriverService = Depends(get_driver_service),
) -> Response[DriverRead]:
    driver = await service.get(driver_id)

    if driver is None:
        raise HTTPException(
            status_code=404,
            detail=f"Driver {driver_id} not found",
        )

    return Response[DriverRead](data=DriverRead.model_validate(driver))
