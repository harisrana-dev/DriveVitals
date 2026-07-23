"""
Runtime State.

Transient state that exists only while a vehicle is actively running
a trip. This is deliberately separate from the persistent Vehicle
model:

    Vehicle       = long-term identity and lifetime state
                    (odometer, fuel level, engine status)

    RuntimeState  = temporary active driving state
                    (current speed, current RPM, ... this trip's
                    distance so far)

If the vehicle stops running, RuntimeState can be discarded; Vehicle
must not be.
"""

from dataclasses import dataclass


@dataclass
class RuntimeState:
    current_speed_kmh: float = 0.0
    current_rpm: float = 0.0
    current_fuel_rate_lph: float = 0.0
    current_engine_temperature_c: float = 20.0  # ambient starting point
    current_trip_distance_km: float = 0.0

    def reset(self) -> None:
        self.current_speed_kmh = 0.0
        self.current_rpm = 0.0
        self.current_fuel_rate_lph = 0.0
        self.current_engine_temperature_c = 20.0
        self.current_trip_distance_km = 0.0