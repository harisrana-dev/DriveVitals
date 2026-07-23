"""
Vehicle Condition model.

Persistent, per-vehicle condition data intended to support future
maintenance analysis. No wear prediction logic lives here — this is
just the data shape.
"""

from dataclasses import dataclass


@dataclass
class VehicleCondition:
    vehicle_id: str
    brake_wear_percent: float = 0.0
    tire_wear_percent: float = 0.0
    engine_condition_percent: float = 100.0
    last_service_odometer_km: float = 0.0