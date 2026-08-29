from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.websocket.alerts import (
    publish_alert_row,
)
from backend.api.v1.dependencies import (
    get_alert_service,
    require_operator_or_admin,
    validate_pagination,
)
from backend.api.v1.schemas.alert import AlertRead
from backend.api.v1.schemas.common import PaginatedResponse
from backend.api.v1.services.alert_service import AlertService
from backend.db.models.user import User

router = APIRouter(prefix="/alerts")


@router.get(
    "",
    response_model=PaginatedResponse[AlertRead],
    summary="List alerts",
    description=(
        "Return a paginated list of alerts. Optionally filter by severity, "
        "type, acknowledgement status, status, category, driver, and time range."
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
    status: str | None = Query(
        default=None,
        description="Filter alerts by status (active, resolved).",
    ),
    category: str | None = Query(
        default=None,
        description="Filter alerts by category.",
    ),
    driver_id: str | None = Query(
        default=None,
        description="Filter alerts by driver ID.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Filter alerts created after this timestamp (ISO 8601).",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="Filter alerts created before this timestamp (ISO 8601).",
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
        status=status,
        category=category,
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[AlertRead](
        data=[AlertRead.model_validate(alert) for alert in alerts],
        count=count,
    )


@router.get(
    "/stats",
    summary="Get alert statistics",
    description=(
        "Return aggregate statistics for alerts matching the optional filters. "
        "Includes total count, critical/high severity counts, active, acknowledged, and resolved counts."
    ),
    tags=["Alerts"],
)
async def alert_stats(
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
    status: str | None = Query(
        default=None,
        description="Filter alerts by status (active, resolved).",
    ),
    category: str | None = Query(
        default=None,
        description="Filter alerts by category.",
    ),
    driver_id: str | None = Query(
        default=None,
        description="Filter alerts by driver ID.",
    ),
    vehicle_id: str | None = Query(
        default=None,
        description="Filter alerts by vehicle ID.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Filter alerts created after this timestamp (ISO 8601).",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="Filter alerts created before this timestamp (ISO 8601).",
    ),
    service: AlertService = Depends(get_alert_service),
) -> dict:
    stats = await service.stats(
        vehicle_id=vehicle_id,
        severity=severity,
        alert_type=type,
        acknowledged=acknowledged,
        status=status,
        category=category,
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
    )
    return stats


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
    status: str | None = Query(
        default=None,
        description="Filter alerts by status (active, resolved).",
    ),
    category: str | None = Query(
        default=None,
        description="Filter alerts by category.",
    ),
    driver_id: str | None = Query(
        default=None,
        description="Filter alerts by driver ID.",
    ),
    start_time: datetime | None = Query(
        default=None,
        description="Filter alerts created after this timestamp (ISO 8601).",
    ),
    end_time: datetime | None = Query(
        default=None,
        description="Filter alerts created before this timestamp (ISO 8601).",
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
        status=status,
        category=category,
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[AlertRead](
        data=[AlertRead.model_validate(alert) for alert in alerts],
        count=count,
    )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertRead,
    summary="Acknowledge an alert",
    description=(
        "Mark an alert as acknowledged. Acknowledged alerts stay visible "
        "until their condition clears (auto-resolve) or they are manually "
        "resolved."
    ),
    tags=["Alerts"],
)
async def acknowledge_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(require_operator_or_admin),
) -> AlertRead:
    alert = await service.acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    publish_alert_row("alert_acknowledged", alert)
    return AlertRead.model_validate(alert)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertRead,
    summary="Resolve an alert",
    description=(
        "Mark an alert as resolved. The alert is preserved in history and "
        "no longer surfaces as active."
    ),
    tags=["Alerts"],
)
async def resolve_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
    current_user: User = Depends(require_operator_or_admin),
) -> AlertRead:
    alert = await service.resolve(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    publish_alert_row("alert_resolved", alert)
    return AlertRead.model_validate(alert)
