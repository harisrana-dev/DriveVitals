from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.security import authenticate_session
from backend.api.v1.services.alert_service import AlertService
from backend.api.v1.services.auth_service import AuthService
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

from backend.db.models.user import User
from backend.db.repositories import (
    AlertRepository,
    AuthSessionRepository,
    DriverRepository,
    DriverStatisticsRepository,
    MaintenanceRepository,
    RouteRepository,
    TelemetryRepository,
    TripRepository,
    UserRepository,
    VehicleHealthRepository,
    VehicleRepository,
)
from backend.db.session import get_session

LIMIT_MIN = 1
LIMIT_MAX = 500

INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

_bearer = HTTPBearer(auto_error=False)


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


async def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(
        UserRepository(session),
        AuthSessionRepository(session),
    )


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_OR_EXPIRED_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = _extract_token(credentials)
    user = await authenticate_session(session, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_OR_EXPIRED_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user_id(current_user: User = Depends(get_current_user)) -> str:
    return current_user.user_id


async def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require a valid authenticated session.

    Equivalent to :func:`get_current_user`; named dependency for
    authorization-focused endpoints.
    """
    return current_user


def require_role(*roles: str):
    """Build a dependency that requires one of the given roles.

    An authenticated user without a required role receives a 403
    ``INSUFFICIENT_PERMISSIONS`` — never a 401, which is reserved for
    unauthenticated requests.
    """

    async def _require(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=INSUFFICIENT_PERMISSIONS,
            )
        return current_user

    return _require


require_admin = require_role("admin")
require_operator_or_admin = require_role("operator", "admin")
