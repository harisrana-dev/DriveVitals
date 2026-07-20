"""Abstract sensor interface and sensor-provider contract.

Defines the `Sensor` abstraction every concrete sensor implements, and
the `SensorProvider` Protocol any provider of sensor readings (virtual,
or a future real-hardware provider) is expected to satisfy. Neither of
these types reads `VehicleState` themselves, mutates anything, or knows
about telemetry formatting -- they are pure contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Protocol, runtime_checkable

from digital_twin.entities.vehicle import Vehicle, VehicleState
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors.pid_mapper import PidMetadata
from digital_twin.sensors.sensor_models import SensorReading


class Sensor(ABC):
    """Abstract base for every sensor in the Virtual Sensor Framework.

    A sensor observes `VehicleState` and produces a `SensorReading`. It
    never mutates `Vehicle`, `VehicleState`, or anything else it is
    given, never generates telemetry, and never makes driving
    decisions -- it is a pure observer.
    """

    @property
    @abstractmethod
    def sensor_name(self) -> str:
        """str: This sensor's unique, stable name (e.g. "vehicle_speed")."""
        raise NotImplementedError

    @property
    @abstractmethod
    def unit(self) -> str:
        """str: Unit of measurement for this sensor's readings."""
        raise NotImplementedError

    @property
    def pid(self) -> PidMetadata | None:
        """PidMetadata | None: PID metadata for this sensor, if applicable.

        Returns `None` by default; concrete sensors with a PID mapping
        override this.
        """
        return None

    @abstractmethod
    def read(
        self, vehicle: Vehicle, state: VehicleState, tick_context: TickContext
    ) -> SensorReading:
        """Observe current vehicle state and produce a reading.

        Args:
            vehicle: The vehicle being observed. Read only.
            state: The vehicle's current state (`vehicle.state`, passed
                explicitly so a sensor's dependency is obvious from its
                signature). Read only.
            tick_context: The simulation's immutable per-tick context,
                used to timestamp the reading.

        Returns:
            The resulting SensorReading. Never mutates `vehicle`,
            `state`, or `tick_context`.
        """
        raise NotImplementedError


@runtime_checkable
class SensorProvider(Protocol):
    """Contract for anything that owns a set of sensors and reads them all.

    `VirtualSensorProvider` is the concrete implementation for this
    sprint; this Protocol exists so a future real-hardware sensor
    provider (reading from actual OBD-II devices) can satisfy the same
    contract without either provider depending on the other.
    """

    def update_all(
        self, vehicle: Vehicle, tick_context: TickContext
    ) -> Iterable[SensorReading]:
        """Read every owned sensor for the current tick.

        Args:
            vehicle: The vehicle to observe.
            tick_context: The simulation's immutable per-tick context.

        Returns:
            One SensorReading per owned sensor.
        """
        ...