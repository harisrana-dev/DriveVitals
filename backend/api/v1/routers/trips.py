from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.v1.dependencies import (
    get_trip_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.trip import TripRead
from backend.api.v1.services.trip_service import TripService

router = APIRouter(prefix="/trips")


@router.get(
    "",
    response_model=PaginatedResponse[TripRead],
    summary="List trips",
    description=(
        "Return a paginated list of trips. Optionally filter by vehicle, "
        "driver and completion status."
    ),
    tags=["Trips"],
)
async def list_trips(
    vehicle_id: str | None = Query(
        default=None,
        description="Filter trips by vehicle id.",
    ),
    driver_id: str | None = Query(
        default=None,
        description="Filter trips by driver id.",
    ),
    completed: bool | None = Query(
        default=None,
        description="Filter trips by completion status.",
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of trips to return.",
    ),
    offset: int = Query(
        default=0,
        description="Number of trips to skip before returning results.",
    ),
    service: TripService = Depends(get_trip_service),
) -> PaginatedResponse[TripRead]:
    limit, offset = validate_pagination(limit, offset)

    trips, count = await service.list(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        completed=completed,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[TripRead](
        data=[TripRead.from_trip(trip) for trip in trips],
        count=count,
    )


@router.get(
    "/{trip_id}",
    response_model=Response[TripRead],
    summary="Get a trip",
    description="Return a single trip by its id.",
    tags=["Trips"],
)
async def get_trip(
    trip_id: str,
    service: TripService = Depends(get_trip_service),
) -> Response[TripRead]:
    trip = await service.get(trip_id)

    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trip {trip_id} not found",
        )

    return Response[TripRead](data=TripRead.from_trip(trip))
