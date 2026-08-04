from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.v1.services.alert_service import AlertService
from backend.api.v1.services.driver_service import DriverService
from backend.api.v1.services.driver_statistics_service import (
    DriverStatisticsService,
)
from backend.api.v1.services.maintenance_service import MaintenanceService
from backend.api.v1.services.route_service import RouteService
from backend.api.v1.services.telemetry_service import TelemetryService
from backend.api.v1.services.trip_service import TripService
from backend.api.v1.services.vehicle_health_service import (
    VehicleHealthService,
)
from backend.api.v1.services.vehicle_service import VehicleService

from backend.db.repositories import (
    AlertRepository,
    DriverRepository,
    DriverStatisticsRepository,
    MaintenanceRepository,
    RouteRepository,
    TelemetryRepository,
    TripRepository,
    VehicleHealthRepository,
    VehicleRepository,
)
from backend.db.session import get_session

LIMIT_MIN = 1
LIMIT_MAX = 500


def validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < LIMIT_MIN or limit > LIMIT_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"limit must be between {LIMIT_MIN} and {LIMIT_MAX}",
        )
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be greater than or equal to 0",
        )
    return limit, offset


async def get_vehicle_service(
    session: AsyncSession = Depends(get_session),
) -> VehicleService:
    return VehicleService(VehicleRepository(session))


async def get_driver_service(
    session: AsyncSession = Depends(get_session),
) -> DriverService:
    return DriverService(DriverRepository(session))


async def get_route_service(
    session: AsyncSession = Depends(get_session),
) -> RouteService:
    return RouteService(RouteRepository(session))


async def get_trip_service(
    session: AsyncSession = Depends(get_session),
) -> TripService:
    return TripService(TripRepository(session))


async def get_telemetry_service(
    session: AsyncSession = Depends(get_session),
) -> TelemetryService:
    return TelemetryService(TelemetryRepository(session))


async def get_vehicle_health_service(
    session: AsyncSession = Depends(get_session),
) -> VehicleHealthService:
    return VehicleHealthService(VehicleHealthRepository(session))


async def get_driver_statistics_service(
    session: AsyncSession = Depends(get_session),
) -> DriverStatisticsService:
    return DriverStatisticsService(DriverStatisticsRepository(session))


async def get_maintenance_service(
    session: AsyncSession = Depends(get_session),
) -> MaintenanceService:
    return MaintenanceService(MaintenanceRepository(session))


async def get_alert_service(
    session: AsyncSession = Depends(get_session),
) -> AlertService:
    return AlertService(AlertRepository(session))
