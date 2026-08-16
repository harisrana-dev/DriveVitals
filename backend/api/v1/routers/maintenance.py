from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_maintenance_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse
from backend.api.v1.schemas.maintenance import (
    MaintenanceCompleteRequest,
    MaintenanceRead,
)
from backend.api.v1.services.maintenance_service import MaintenanceService
from backend.api.v1.services.maintenance_service import VALID_SORTS

router = APIRouter(prefix="/maintenance")


@router.get(
    "",
    response_model=PaginatedResponse[MaintenanceRead],
    summary="List maintenance records",
    description=(
        "Return a paginated list of maintenance records. Optionally filter "
        "by vehicle, priority, component and status."
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
    status: str | None = Query(
        default=None,
        description="Filter maintenance records by status "
        "(pending, completed).",
    ),
    sort: str | None = Query(
        default="created_at",
        description="Sort order: created_at, priority, due_odometer_km, "
        "due_date.",
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
    sort = sort if sort in VALID_SORTS else "created_at"

    records, count = await service.list(
        vehicle_id=vehicle_id,
        priority=priority,
        component=component,
        status=status,
        sort=sort,
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
        "vehicle. Optionally filter by priority, component and status."
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
    status: str | None = Query(
        default=None,
        description="Filter maintenance records by status "
        "(pending, completed).",
    ),
    sort: str | None = Query(
        default="created_at",
        description="Sort order: created_at, priority, due_odometer_km, "
        "due_date.",
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
    sort = sort if sort in VALID_SORTS else "created_at"

    records, count = await service.list(
        vehicle_id=vehicle_id,
        priority=priority,
        component=component,
        status=status,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[MaintenanceRead](
        data=[MaintenanceRead.model_validate(record) for record in records],
        count=count,
    )


@router.patch(
    "/{maintenance_id}/complete",
    response_model=MaintenanceRead,
    summary="Mark a maintenance record as completed",
    description=(
        "Set a maintenance record status to completed, recording when the "
        "work was done. Idempotent: completing an already-completed record "
        "returns it unchanged."
    ),
    tags=["Maintenance"],
)
async def complete_maintenance(
    maintenance_id: str,
    payload: MaintenanceCompleteRequest,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MaintenanceRead:
    record = await service.complete(
        maintenance_id=maintenance_id,
        completed_odometer_km=payload.completed_odometer_km,
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Maintenance record not found",
        )
    return MaintenanceRead.model_validate(record)
