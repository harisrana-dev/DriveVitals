from fastapi import APIRouter

from backend.api.v1.routers import (
    alerts_router,
    driver_statistics_router,
    drivers_router,
    maintenance_router,
    routes_router,
    system_router,
    telemetry_router,
    trips_router,
    vehicle_health_router,
    vehicles_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(vehicles_router)
api_router.include_router(drivers_router)
api_router.include_router(routes_router)
api_router.include_router(trips_router)
api_router.include_router(telemetry_router)
api_router.include_router(vehicle_health_router)
api_router.include_router(driver_statistics_router)
api_router.include_router(maintenance_router)
api_router.include_router(alerts_router)
api_router.include_router(system_router)

__all__ = ["api_router"]
