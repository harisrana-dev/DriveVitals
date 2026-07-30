from backend.db.repositories.vehicle_repository import VehicleRepository
from backend.db.repositories.driver_repository import DriverRepository
from backend.db.repositories.route_repository import RouteRepository
from backend.db.repositories.trip_repository import TripRepository
from backend.db.repositories.telemetry_repository import TelemetryRepository
from backend.db.repositories.behaviour_repository import BehaviourRepository
from backend.db.repositories.vehicle_health_repository import VehicleHealthRepository
from backend.db.repositories.alert_repository import AlertRepository
from backend.db.repositories.maintenance_repository import MaintenanceRepository

__all__ = [
    "VehicleRepository",
    "DriverRepository",
    "RouteRepository",
    "TripRepository",
    "TelemetryRepository",
    "BehaviourRepository",
    "VehicleHealthRepository",
    "AlertRepository",
    "MaintenanceRepository",
]
