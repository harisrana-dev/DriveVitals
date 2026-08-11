from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response as FastAPIResponse,
    status,
)

from backend.api.v1.dependencies import (
    get_trip_service,
    validate_pagination,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.trip import TripDeleteResult, TripRead
from backend.api.v1.services.trip_service import TripLifecycleError, TripService

router = APIRouter(prefix="/trips")


@router.get(
    "",
    response_model=PaginatedResponse[TripRead],
    summary="List trips",
    description=(
        "Return a paginated list of trips. Optionally filter by vehicle, "
        "driver, route type and trip status."
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
    status: str | None = Query(
        default=None,
        description=(
            "Filter trips by one or more comma-separated statuses "
            "(assigned, started, in_progress, completed, aborted). "
            "When present, takes precedence over `completed`."
        ),
    ),
    route_type: str | None = Query(
        default=None,
        description="Filter trips by route type (urban, highway, rural).",
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

    statuses = None
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]

    trips, count = await service.list(
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        completed=completed,
        statuses=statuses,
        route_type=route_type,
        limit=limit,
        offset=offset,
    )

    return PaginatedResponse[TripRead](
        data=[TripRead.from_trip(trip) for trip in trips],
        count=count,
    )


@router.delete(
    "/aborted",
    response_model=TripDeleteResult,
    summary="Delete all aborted trips",
    description=(
        "Permanently delete every aborted trip together with its "
        "trip-scoped telemetry, behaviour events and alerts. Vehicles, "
        "drivers and routes are preserved. Returns the number of trips "
        "deleted (0 when none are aborted)."
    ),
    tags=["Trips"],
)
async def delete_all_aborted_trips(
    service: TripService = Depends(get_trip_service),
) -> TripDeleteResult:
    deleted_count = await service.delete_all_aborted()
    return TripDeleteResult(deleted_count=deleted_count)


@router.delete(
    "/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an aborted trip",
    description=(
        "Permanently delete a single trip and its trip-scoped telemetry, "
        "behaviour events and alerts. Only trips in the `aborted` status "
        "can be deleted; completed and in-progress trips are rejected."
    ),
    tags=["Trips"],
)
async def delete_trip(
    trip_id: str,
    service: TripService = Depends(get_trip_service),
) -> FastAPIResponse:
    try:
        trip = await service.delete_aborted(trip_id)
    except TripLifecycleError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Trip {trip_id} cannot be deleted while status is "
                f"'{exc.status}'. Only aborted trips can be deleted."
            ),
        ) from exc

    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip {trip_id} not found",
        )

    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)


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
