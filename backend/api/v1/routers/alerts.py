from fastapi import APIRouter, Depends, Query

from backend.api.v1.dependencies import (
    get_alert_service,
    validate_pagination,
)
from backend.api.v1.schemas.alert import AlertRead
from backend.api.v1.schemas.common import PaginatedResponse
from backend.api.v1.services.alert_service import AlertService

router = APIRouter(prefix="/alerts")


@router.get(
    "",
    response_model=PaginatedResponse[AlertRead],
    summary="List alerts",
    description=(
        "Return a paginated list of alerts. Optionally filter by severity, "
        "type and acknowledgement status."
    ),
    tags=["Alerts"],
)
async def list_alerts(
    severity: str | None = Query(
        default=None,
        description="Filter alerts by severity.",
    ),
    type: str | None = Query(
        default=None,
        description="Filter alerts by alert type.",
    ),
    acknowledged: bool | None = Query(
        default=None,
        description="Filter alerts by acknowledgement status.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of alerts to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of alerts to skip before returning results.",
    ),
    service: AlertService = Depends(get_alert_service),
) -> PaginatedResponse[AlertRead]:
    limit, offset = validate_pagination(limit, offset)

    alerts, count = await service.list(
        vehicle_id=None,
        severity=severity,
        alert_type=type,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[AlertRead](
        data=[AlertRead.model_validate(alert) for alert in alerts],
        count=count,
    )


@router.get(
    "/{vehicle_id}",
    response_model=PaginatedResponse[AlertRead],
    summary="List alerts for a vehicle",
    description=(
        "Return a paginated list of alerts for a single vehicle. Optionally "
        "filter by severity, type and acknowledgement status."
    ),
    tags=["Alerts"],
)
async def list_vehicle_alerts(
    vehicle_id: str,
    severity: str | None = Query(
        default=None,
        description="Filter alerts by severity.",
    ),
    type: str | None = Query(
        default=None,
        description="Filter alerts by alert type.",
    ),
    acknowledged: bool | None = Query(
        default=None,
        description="Filter alerts by acknowledgement status.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of alerts to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of alerts to skip before returning results.",
    ),
    service: AlertService = Depends(get_alert_service),
) -> PaginatedResponse[AlertRead]:
    limit, offset = validate_pagination(limit, offset)

    alerts, count = await service.list(
        vehicle_id=vehicle_id,
        severity=severity,
        alert_type=type,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[AlertRead](
        data=[AlertRead.model_validate(alert) for alert in alerts],
        count=count,
    )
