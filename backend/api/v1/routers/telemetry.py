from fastapi import APIRouter, Depends, Query

from backend.api.v1.dependencies import (
    get_telemetry_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse
from backend.api.v1.schemas.telemetry import TelemetryRead
from backend.api.v1.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/telemetry")


@router.get(
    "",
    response_model=PaginatedResponse[TelemetryRead],
    summary="List telemetry samples",
    description=(
        "Return a paginated list of telemetry samples across all vehicles. "
        "Use latest=true to return only the newest sample per vehicle."
    ),
    tags=["Telemetry"],
)
async def list_telemetry(
    latest: bool = Query(
        default=False,
        description="Return only the newest sample per vehicle.",
    ),
    trip_id: str | None = Query(
        default=None,
        description="Filter samples to a single trip.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of samples to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of samples to skip before returning results.",
    ),
    service: TelemetryService = Depends(get_telemetry_service),
) -> PaginatedResponse[TelemetryRead]:
    limit, offset = validate_pagination(limit, offset)

    samples, count = await service.list(
        vehicle_id=None,
        trip_id=trip_id,
        latest=latest,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[TelemetryRead](
        data=[TelemetryRead.model_validate(sample) for sample in samples],
        count=count,
    )


@router.get(
    "/{vehicle_id}",
    response_model=PaginatedResponse[TelemetryRead],
    summary="List telemetry samples for a vehicle",
    description=(
        "Return a paginated list of telemetry samples for a single vehicle, "
        "newest first. Use latest=true to return only the newest sample."
    ),
    tags=["Telemetry"],
)
async def list_vehicle_telemetry(
    vehicle_id: str,
    latest: bool = Query(
        default=False,
        description="Return only the newest sample for the vehicle.",
    ),
    trip_id: str | None = Query(
        default=None,
        description="Filter samples to a single trip.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of samples to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of samples to skip before returning results.",
    ),
    service: TelemetryService = Depends(get_telemetry_service),
) -> PaginatedResponse[TelemetryRead]:
    limit, offset = validate_pagination(limit, offset)

    samples, count = await service.list(
        vehicle_id=vehicle_id,
        trip_id=trip_id,
        latest=latest,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[TelemetryRead](
        data=[TelemetryRead.model_validate(sample) for sample in samples],
        count=count,
    )
