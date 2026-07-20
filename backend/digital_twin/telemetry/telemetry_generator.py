"""TelemetryGenerator: packages SensorReadings into a TelemetryPacket.

Consumes the existing sensor reading models (`SensorReading` and its
subclasses) exactly as produced by `VirtualSensorProvider` -- no second
sensor abstraction, no duplicated reading types. Deterministic: the
only internal state is a plain monotonically incrementing counter used
for `TelemetryPacket.sequence_number`, never a source of randomness.
"""

from __future__ import annotations

from typing import Iterable

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.entities.vehicle import Vehicle
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors.sensor_models import SensorReading
from digital_twin.telemetry.telemetry_packet import TelemetryPacket


class TelemetryGenerator:
    """Constructs TelemetryPackets from a vehicle's sensor readings.

    Each instance owns its own sequence counter, so two independent
    `TelemetryGenerator` instances (e.g. one per vehicle, if a future
    integration wants that) never share or race on sequencing state.
    """

    def __init__(self) -> None:
        """Initialize the generator with its sequence counter at zero."""
        self._next_sequence_number = 0

    def generate(
        self,
        vehicle: Vehicle,
        sensor_readings: Iterable[SensorReading],
        tick_context: TickContext,
    ) -> TelemetryPacket:
        """Package one tick's sensor readings into a TelemetryPacket.

        Args:
            vehicle: The vehicle these readings belong to. Read only --
                `vehicle` and `vehicle.state` are never modified.
            sensor_readings: The SensorReadings for this tick, typically
                the result of `VirtualSensorProvider.update_all()`.
                Consumed as-is: every reading (including any with
                `valid=False`) is preserved unchanged in the resulting
                packet, never filtered, replaced, or "fixed up".
            tick_context: The simulation's immutable per-tick context;
                supplies `tick_id` and `simulation_time`.

        Returns:
            The resulting TelemetryPacket.

        Raises:
            ConfigurationError: If `vehicle.vehicle_id` is empty, or
                `sensor_readings` is empty. Both are also enforced by
                `TelemetryPacket.__post_init__`, but are checked here
                first with a message tied to the generator's own
                inputs rather than the packet's.
        """
        readings_tuple = tuple(sensor_readings)
        if not readings_tuple:
            raise ConfigurationError(
                "TelemetryGenerator.generate() received no sensor readings; "
                "cannot construct a TelemetryPacket with zero observations."
            )
        if not vehicle.vehicle_id:
            raise ConfigurationError(
                "TelemetryGenerator.generate() received a vehicle with an empty vehicle_id."
            )

        packet = TelemetryPacket(
            vehicle_id=vehicle.vehicle_id,
            tick_id=tick_context.tick_id,
            simulation_time=tick_context.simulation_time,
            sequence_number=self._next_sequence_number,
            sensor_readings=readings_tuple,
        )
        self._next_sequence_number += 1
        return packet