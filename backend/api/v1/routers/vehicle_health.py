from fastapi import APIRouter, Depends, HTTPException, Query

from backend.analytics.vehicle_health.health_config import (
    health_config_to_dict,
)
from backend.api.v1.dependencies import (
    get_vehicle_health_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.vehicle_health import VehicleHealthRead
from backend.api.v1.services.vehicle_health_service import VehicleHealthService

router = APIRouter(prefix="/vehicle-health")


@router.get(
    "/config",
    response_model=Response[dict],
    summary="Get health configuration",
    description=(
        "Return the canonical health thresholds and subsystem weights "
        "consumed by the vehicle health engine."
    ),
    tags=["Vehicle Health"],
)
async def get_health_config() -> Response[dict]:
    return Response[dict](data=health_config_to_dict())


@router.get(
    "",
    response_model=PaginatedResponse[VehicleHealthRead],
    summary="List vehicle health",
    description="Return a paginated list of vehicle health records.",
    tags=["Vehicle Health"],
)
async def list_vehicle_health(
    limit: int = Query(
        default=100,
        description="Maximum number of records to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of records to skip before returning results.",
    ),
    service: VehicleHealthService = Depends(get_vehicle_health_service),
) -> PaginatedResponse[VehicleHealthRead]:
    limit, offset = validate_pagination(limit, offset)

    records, count = await service.list(
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[VehicleHealthRead](
        data=[VehicleHealthRead.model_validate(record) for record in records],
        count=count,
    )


@router.get(
    "/{vehicle_id}",
    response_model=Response[VehicleHealthRead],
    summary="Get vehicle health",
    description="Return the vehicle health record for a single vehicle.",
    tags=["Vehicle Health"],
)
async def get_vehicle_health(
    vehicle_id: str,
    service: VehicleHealthService = Depends(get_vehicle_health_service),
) -> Response[VehicleHealthRead]:
    record = await service.get(vehicle_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle health for {vehicle_id} not found",
        )

    return Response[VehicleHealthRead](
        data=VehicleHealthRead.model_validate(record)
    )
