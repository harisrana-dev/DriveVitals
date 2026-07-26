"""
Runtime State Store.

Maintains the latest RuntimeAnalyticsState for every active vehicle,
keyed by vehicle_id. Accepts TelemetrySamples and keeps the in-memory
mapping current. This is a pure state container — it performs no
analysis, scoring, or persistence.
"""

from backend.analytics.state.runtime_state import RuntimeAnalyticsState
from backend.telemetry.models.telemetry_sample import TelemetrySample


class RuntimeStateStore:
    """In-memory store of the latest runtime state per vehicle."""

    def __init__(self) -> None:
        self._states: dict[str, RuntimeAnalyticsState] = {}

    def update(self, sample: TelemetrySample) -> RuntimeAnalyticsState:
        state = RuntimeAnalyticsState(
            vehicle_id=sample.vehicle_id,
            driver_id=sample.driver_id,
            trip_id=sample.trip_id,
            timestamp=sample.timestamp,
            speed_kmh=sample.speed_kmh,
            rpm=sample.rpm,
            throttle_position_percent=sample.throttle_position_percent,
            brake_pressure=sample.brake_pressure,
            coolant_temperature_c=sample.coolant_temperature_c,
            engine_load_percent=sample.engine_load_percent,
            fuel_rate_lph=sample.fuel_rate_lph,
            fuel_level_percent=sample.fuel_level_percent,
            odometer_km=sample.odometer_km,
        )
        self._states[sample.vehicle_id] = state
        return state

    def get(self, vehicle_id: str) -> RuntimeAnalyticsState | None:
        return self._states.get(vehicle_id)

    def remove(self, vehicle_id: str) -> None:
        self._states.pop(vehicle_id, None)

    def clear(self) -> None:
        self._states.clear()

    def all_states(self) -> list[RuntimeAnalyticsState]:
        return list(self._states.values())

    def __len__(self) -> int:
        return len(self._states)
