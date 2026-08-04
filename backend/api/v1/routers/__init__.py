from backend.api.v1.routers.alerts import router as alerts_router
from backend.api.v1.routers.driver_statistics import (
    router as driver_statistics_router,
)
from backend.api.v1.routers.drivers import router as drivers_router
from backend.api.v1.routers.maintenance import router as maintenance_router
from backend.api.v1.routers.routes import router as routes_router
from backend.api.v1.routers.system import router as system_router
from backend.api.v1.routers.telemetry import router as telemetry_router
from backend.api.v1.routers.trips import router as trips_router
from backend.api.v1.routers.vehicle_health import (
    router as vehicle_health_router,
)
from backend.api.v1.routers.vehicles import router as vehicles_router

__all__ = [
    "alerts_router",
    "driver_statistics_router",
    "drivers_router",
    "maintenance_router",
    "routes_router",
    "system_router",
    "telemetry_router",
    "trips_router",
    "vehicle_health_router",
    "vehicles_router",
]
