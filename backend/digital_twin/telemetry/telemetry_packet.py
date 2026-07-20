"""Immutable telemetry packet produced from one simulation tick.

A TelemetryPacket is the internal contract between the Digital Twin's
sensor layer and future telemetry consumers such as API, database, or
streaming adapters.

This module intentionally contains no transport, persistence, analytics,
or networking logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.sensors.sensor_models import SensorReading


@dataclass(frozen=True, slots=True)
class TelemetryPacket:
    """Immutable snapshot of sensor observations for one simulation tick.

    A packet contains the sensor readings observed for one vehicle at one
    simulation tick together with the metadata required to identify and
    order that snapshot.

    Attributes:
        vehicle_id: Identifier of the vehicle that produced the readings.
        tick_id: Simulation tick associated with this packet.
        simulation_time: Simulated timestamp associated with the packet.
        sequence_number: Monotonically increasing sequence number assigned
            by the TelemetryGenerator instance that created the packet.
        sensor_readings: Immutable tuple of sensor observations.
    """

    vehicle_id: str
    tick_id: int
    simulation_time: datetime
    sequence_number: int
    sensor_readings: tuple[SensorReading, ...]

    def __post_init__(self) -> None:
        """Validate packet invariants.

        Raises:
            ConfigurationError: If required metadata is invalid or the
                packet contains no sensor observations.
        """
        if not self.vehicle_id:
            raise ConfigurationError(
                "TelemetryPacket.vehicle_id cannot be empty."
            )

        if self.tick_id < 0:
            raise ConfigurationError(
                "TelemetryPacket.tick_id cannot be negative."
            )

        if self.sequence_number < 0:
            raise ConfigurationError(
                "TelemetryPacket.sequence_number cannot be negative."
            )

        if not self.sensor_readings:
            raise ConfigurationError(
                "TelemetryPacket.sensor_readings cannot be empty."
            )

        if not isinstance(self.sensor_readings, tuple):
            raise ConfigurationError(
                "TelemetryPacket.sensor_readings must be an immutable tuple."
            )