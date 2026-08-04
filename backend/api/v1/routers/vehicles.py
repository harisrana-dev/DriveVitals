from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_vehicle_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.vehicle import VehicleRead
from backend.api.v1.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles")


@router.get(
    "",
    response_model=PaginatedResponse[VehicleRead],
    summary="List vehicles",
    description=(
        "Return a paginated list of vehicles. Optionally filter by status "
        "or by the driver assigned through a trip."
    ),
    tags=["Vehicles"],
)
async def list_vehicles(
    status: str | None = Query(
        default=None,
        description="Filter vehicles by status.",
    ),
    driver: str | None = Query(
        default=None,
        description="Filter vehicles that have a trip with this driver id.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of vehicles to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of vehicles to skip before returning results.",
    ),
    service: VehicleService = Depends(get_vehicle_service),
) -> PaginatedResponse[VehicleRead]:
    limit, offset = validate_pagination(limit, offset)

    vehicles, count = await service.list(
        status=status,
        driver=driver,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[VehicleRead](
        data=[VehicleRead.model_validate(vehicle) for vehicle in vehicles],
        count=count,
    )


@router.get(
    "/{vehicle_id}",
    response_model=Response[VehicleRead],
    summary="Get a vehicle",
    description="Return a single vehicle by its id.",
    tags=["Vehicles"],
)
async def get_vehicle(
    vehicle_id: str,
    service: VehicleService = Depends(get_vehicle_service),
) -> Response[VehicleRead]:
    vehicle = await service.get(vehicle_id)

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle {vehicle_id} not found",
        )

    return Response[VehicleRead](data=VehicleRead.model_validate(vehicle))
