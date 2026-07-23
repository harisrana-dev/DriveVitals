"""
Vehicle model.

Represents a persistent fleet asset. Holds only long-term identity and
lifetime operational state (odometer, fuel level, engine status).

This model intentionally contains NO telemetry generation logic,
NO analytics logic, and NO database/persistence code. It is a plain
data holder that other layers (runtime, persistence) read and update.
"""

from dataclasses import dataclass
from enum import Enum


class EngineStatus(str, Enum):
    OFF = "off"
    IDLE = "idle"
    RUNNING = "running"


@dataclass
class Vehicle:
    vehicle_id: str
    make: str
    model: str
    year: int

    # Lifetime operational state. Conceptually persistent: if the
    # application restarts, these values must be reloaded from storage
    # rather than reset to defaults.
    odometer_km: float = 0.0
    fuel_level_percent: float = 100.0
    engine_status: EngineStatus = EngineStatus.OFF

    def start_engine(self) -> None:
        self.engine_status = EngineStatus.RUNNING

    def stop_engine(self) -> None:
        self.engine_status = EngineStatus.OFF

    def advance_odometer(self, delta_km: float) -> None:
        """Increase the lifetime odometer reading. Never decreases."""
        if delta_km < 0:
            raise ValueError("Odometer cannot move backwards")
        self.odometer_km += delta_km

    def consume_fuel(self, percent: float) -> None:
        """Reduce fuel level, clamped to [0, 100]."""
        self.fuel_level_percent = max(0.0, min(100.0, self.fuel_level_percent - percent))