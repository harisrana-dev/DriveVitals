"""AnalyticsInput: the normalized boundary between telemetry and analytics.

Analytics modules consume AnalyticsInput, not TelemetryPacket or
SensorReading directly. This keeps the analytics layer decoupled
from the sensor implementation details.

The boundary also carries real per-tick physics metrics and trip/driver
identity from the Digital Twin domain, so analytics can compute fuel
efficiency and trip performance without fabricating data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from digital_twin.sensors.sensor_models import NumericSensorReading
from digital_twin.telemetry.telemetry_packet import TelemetryPacket

try:
    from digital_twin.physics.physics_engine import PhysicsTickResult
except ImportError:
    PhysicsTickResult = None  # type: ignore[assignment,misc]

try:
    from digital_twin.entities.trip import Trip
except ImportError:
    Trip = None  # type: ignore[assignment,misc]

#: Mapping from sensor_name to AnalyticsInput field name.
_SENSOR_MAP: dict[str, str] = {
    "vehicle_speed": "speed_kmh",
    "engine_rpm": "rpm",
    "gear_position": "gear",
    "fuel_level": "fuel_level_percent",
    "engine_load": "engine_load_percent",
    "engine_temperature": "engine_temperature_celsius",
    "battery_voltage": "battery_voltage",
    "odometer": "odometer_km",
    "brake_pad_health": "brake_pad_health_percent",
    "tyre_health": "tyre_health_percent",
    "fuel_rate": "fuel_rate_lph",
}


@dataclass(frozen=True, slots=True)
class AnalyticsInput:
    """Immutable, analytics-facing snapshot of one tick's observations.

    Sensor fields are Optional[float] because sensors may be missing
    or report non-numeric values. Physics fields carry real per-tick
    metrics from the Digital Twin. Trip/driver fields carry domain
    identity when available.
    """

    vehicle_id: str
    tick_id: int
    timestamp: datetime

    # --- Sensor fields (from TelemetryPacket) ---
    speed_kmh: float | None = None
    rpm: float | None = None
    gear: float | None = None
    fuel_level_percent: float | None = None
    fuel_rate_lph: float | None = None
    engine_load_percent: float | None = None
    engine_temperature_celsius: float | None = None
    battery_voltage: float | None = None
    odometer_km: float | None = None
    brake_pad_health_percent: float | None = None
    tyre_health_percent: float | None = None

    # --- Physics fields (from PhysicsTickResult) ---
    distance_travelled_km: float | None = None
    fuel_consumed_liters: float | None = None

    # --- Trip / driver identity (from Digital Twin domain) ---
    trip_id: str | None = None
    driver_id: str | None = None
    distance_planned_km: float | None = None
    distance_completed_km: float | None = None
    duration_minutes: float | None = None
    average_speed_kmh: float | None = None
    fuel_efficiency_km_per_liter: float | None = None

    @classmethod
    def from_packet(
        cls,
        packet: TelemetryPacket,
        physics_result: object | None = None,
        trip: object | None = None,
    ) -> AnalyticsInput:
        """Adapt a TelemetryPacket (plus optional domain context) into AnalyticsInput.

        Extracts numeric sensor values by name. Missing sensors remain None.
        Non-numeric readings are skipped. On duplicate sensor names the
        first occurrence wins.

        Args:
            packet: An immutable TelemetryPacket from the Digital Twin.
            physics_result: Optional PhysicsTickResult with per-tick metrics.
            trip: Optional Trip entity with trip progress data.

        Raises:
            ValueError: If packet.sensor_readings is empty.
        """
        if not packet.sensor_readings:
            raise ValueError(
                "Cannot create AnalyticsInput from a packet "
                "with no sensor readings."
            )

        kwargs: dict[str, float | None] = {}
        seen: set[str] = set()

        for reading in packet.sensor_readings:
            field_name = _SENSOR_MAP.get(reading.sensor_name)
            if field_name is None or field_name in seen:
                continue
            if isinstance(reading, NumericSensorReading) and reading.valid:
                kwargs[field_name] = reading.value
                seen.add(field_name)

        # Physics tick data
        if physics_result is not None:
            kwargs["distance_travelled_km"] = getattr(physics_result, "distance_travelled_km", None)
            kwargs["fuel_consumed_liters"] = getattr(physics_result, "fuel_consumed_liters", None)

        # Trip / driver domain context
        if trip is not None:
            kwargs["trip_id"] = getattr(trip, "trip_id", None)
            kwargs["driver_id"] = getattr(trip, "driver_id", None)
            kwargs["distance_planned_km"] = getattr(trip, "distance_planned_km", None)
            kwargs["distance_completed_km"] = getattr(trip, "distance_completed_km", None)
            kwargs["duration_minutes"] = getattr(trip, "duration_minutes", None)
            kwargs["average_speed_kmh"] = getattr(trip, "average_speed_kmh", None)
            kwargs["fuel_efficiency_km_per_liter"] = getattr(trip, "fuel_efficiency_km_per_liter", None)

        return cls(
            vehicle_id=packet.vehicle_id,
            tick_id=packet.tick_id,
            timestamp=packet.simulation_time,
            **kwargs,
        )
