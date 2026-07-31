from backend.db.models.vehicle import Vehicle
from backend.db.models.driver import Driver
from backend.db.models.route import Route
from backend.db.models.trip import Trip
from backend.db.models.telemetry_sample import TelemetrySample
from backend.db.models.behaviour_event import BehaviourEvent
from backend.db.models.alert import Alert
from backend.db.models.maintenance_record import MaintenanceRecord
from backend.db.models.vehicle_health import VehicleHealth
from backend.db.models.driver_statistics import DriverStatistics
from backend.db.models.vehicle_statistics import VehicleStatistics

__all__ = [
    "Vehicle",
    "Driver",
    "Route",
    "Trip",
    "TelemetrySample",
    "BehaviourEvent",
    "Alert",
    "MaintenanceRecord",
    "VehicleHealth",
    "DriverStatistics",
    "VehicleStatistics",
]
