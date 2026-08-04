from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_driver_statistics_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.driver_statistics import DriverStatisticsRead
from backend.api.v1.services.driver_statistics_service import (
    DriverStatisticsService,
)

router = APIRouter(prefix="/driver-statistics")


@router.get(
    "",
    response_model=PaginatedResponse[DriverStatisticsRead],
    summary="List driver statistics",
    description="Return a paginated list of driver statistics records.",
    tags=["Driver Statistics"],
)
async def list_driver_statistics(
    limit: int = Query(
        default=100,
        description="Maximum number of records to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of records to skip before returning results.",
    ),
    service: DriverStatisticsService = Depends(get_driver_statistics_service),
) -> PaginatedResponse[DriverStatisticsRead]:
    limit, offset = validate_pagination(limit, offset)

    records, count = await service.list(
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[DriverStatisticsRead](
        data=[DriverStatisticsRead.model_validate(record) for record in records],
        count=count,
    )


@router.get(
    "/{driver_id}",
    response_model=Response[DriverStatisticsRead],
    summary="Get driver statistics",
    description="Return the driver statistics record for a single driver.",
    tags=["Driver Statistics"],
)
async def get_driver_statistics(
    driver_id: str,
    service: DriverStatisticsService = Depends(get_driver_statistics_service),
) -> Response[DriverStatisticsRead]:
    record = await service.get(driver_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Driver statistics for {driver_id} not found",
        )

    return Response[DriverStatisticsRead](
        data=DriverStatisticsRead.model_validate(record)
    )
