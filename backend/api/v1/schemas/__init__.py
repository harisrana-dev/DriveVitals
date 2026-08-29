from backend.api.v1.schemas.alert import AlertRead
from backend.api.v1.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UserRead,
    UserWithToken,
)
from backend.api.v1.schemas.common import PaginatedResponse, Response
from backend.api.v1.schemas.driver import DriverRead
from backend.api.v1.schemas.driver_statistics import DriverStatisticsRead
from backend.api.v1.schemas.maintenance import MaintenanceRead
from backend.api.v1.schemas.route import RouteRead
from backend.api.v1.schemas.telemetry import TelemetryRead
from backend.api.v1.schemas.trip import TripRead
from backend.api.v1.schemas.vehicle import VehicleRead
from backend.api.v1.schemas.vehicle_health import VehicleHealthRead

__all__ = [
    "AlertRead",
    "DriverRead",
    "DriverStatisticsRead",
    "LoginRequest",
    "MaintenanceRead",
    "PaginatedResponse",
    "Response",
    "RouteRead",
    "SignupRequest",
    "TelemetryRead",
    "TripRead",
    "UserRead",
    "UserWithToken",
    "VehicleHealthRead",
    "VehicleRead",
]
