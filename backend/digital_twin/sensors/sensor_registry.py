"""SensorRegistry: registers, finds, and iterates sensors.

A plain, instantiable class -- not a singleton. Each
`VirtualSensorProvider` owns its own `SensorRegistry` instance,
injected at construction time, so multiple providers (e.g. one per
vehicle, if ever needed) never share state.
"""

from __future__ import annotations

from typing import Iterator

from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.sensors.sensor_provider import Sensor


class SensorRegistry:
    """Holds a set of Sensor instances, keyed by sensor name.

    Not a singleton: every `SensorRegistry()` call creates an
    independent registry.
    """

    def __init__(self) -> None:
        """Initialize an empty sensor registry."""
        self._sensors: dict[str, Sensor] = {}

    def register(self, sensor: Sensor) -> None:
        """Register a sensor.

        Args:
            sensor: The sensor to register.

        Raises:
            EntityAlreadyExistsError: If a sensor with the same
                `sensor_name` is already registered.
        """
        if sensor.sensor_name in self._sensors:
            raise EntityAlreadyExistsError("Sensor", sensor.sensor_name)
        self._sensors[sensor.sensor_name] = sensor

    def find(self, sensor_name: str) -> Sensor:
        """Look up a registered sensor by name.

        Args:
            sensor_name: Name of the sensor to retrieve.

        Returns:
            The matching Sensor.

        Raises:
            EntityNotFoundError: If no sensor with that name is
                registered.
        """
        sensor = self._sensors.get(sensor_name)
        if sensor is None:
            raise EntityNotFoundError("Sensor", sensor_name)
        return sensor

    def all_sensors(self) -> list[Sensor]:
        """List every registered sensor.

        Returns:
            All registered Sensor instances, in registration order.
        """
        return list(self._sensors.values())

    def __iter__(self) -> Iterator[Sensor]:
        """Iterate over registered sensors, in registration order."""
        return iter(self._sensors.values())

    def __len__(self) -> int:
        """Return the number of registered sensors."""
        return len(self._sensors)