from fastapi import APIRouter, Depends, Query

from backend.api.v1.dependencies import (
    get_maintenance_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse
from backend.api.v1.schemas.maintenance import MaintenanceRead
from backend.api.v1.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance")


@router.get(
    "",
    response_model=PaginatedResponse[MaintenanceRead],
    summary="List maintenance records",
    description=(
        "Return a paginated list of maintenance records. Optionally filter "
        "by vehicle, priority and component."
    ),
    tags=["Maintenance"],
)
async def list_maintenance(
    vehicle_id: str | None = Query(
        default=None,
        description="Filter maintenance records by vehicle id.",
    ),
    priority: str | None = Query(
        default=None,
        description="Filter maintenance records by priority.",
    ),
    component: str | None = Query(
        default=None,
        description="Filter maintenance records by component.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of records to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of records to skip before returning results.",
    ),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> PaginatedResponse[MaintenanceRead]:
    limit, offset = validate_pagination(limit, offset)

    records, count = await service.list(
        vehicle_id=vehicle_id,
        priority=priority,
        component=component,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[MaintenanceRead](
        data=[MaintenanceRead.model_validate(record) for record in records],
        count=count,
    )


@router.get(
    "/{vehicle_id}",
    response_model=PaginatedResponse[MaintenanceRead],
    summary="List maintenance records for a vehicle",
    description=(
        "Return a paginated list of maintenance records for a single "
        "vehicle. Optionally filter by priority and component."
    ),
    tags=["Maintenance"],
)
async def list_vehicle_maintenance(
    vehicle_id: str,
    priority: str | None = Query(
        default=None,
        description="Filter maintenance records by priority.",
    ),
    component: str | None = Query(
        default=None,
        description="Filter maintenance records by component.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of records to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of records to skip before returning results.",
    ),
    service: MaintenanceService = Depends(get_maintenance_service),
) -> PaginatedResponse[MaintenanceRead]:
    limit, offset = validate_pagination(limit, offset)

    records, count = await service.list(
        vehicle_id=vehicle_id,
        priority=priority,
        component=component,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[MaintenanceRead](
        data=[MaintenanceRead.model_validate(record) for record in records],
        count=count,
    )
