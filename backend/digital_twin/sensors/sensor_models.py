"""Immutable sensor reading models.

`SensorReading` is the common base every concrete reading type extends.
All readings are frozen -- a sensor produces a snapshot, never a
mutable object a caller could alter after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from digital_twin.sensors.pid_mapper import PidMetadata


@dataclass(frozen=True)
class SensorReading:
    """Base fields common to every sensor reading.

    Concrete sensors return one of `NumericSensorReading`,
    `BooleanSensorReading`, or `EnumeratedSensorReading` -- never this
    base class directly.

    Attributes:
        sensor_name: Human-readable name of the sensor that produced
            this reading (e.g. "vehicle_speed").
        timestamp: Simulated time this reading was taken, from the
            TickContext the sensor was read with.
        unit: Unit of measurement for `value` (e.g. "km/h", "%"). Empty
            string for unitless readings.
        pid: OBD-II (or DriveVitals custom) PID metadata identifying
            this signal, if one applies. `None` for readings with no
            PID mapping.
        valid: Whether this reading reflects a real, current
            observation. Always `True` for every sensor this sprint
            implements -- see the gap report in
            `virtual_sensor_provider.py` for the requested sensors that
            were *not* implemented (and therefore never produce a
            reading, valid or otherwise) because no VehicleState source
            exists for them.
    """

    sensor_name: str
    timestamp: datetime
    unit: str
    pid: PidMetadata | None
    valid: bool


@dataclass(frozen=True)
class NumericSensorReading(SensorReading):
    """A sensor reading whose value is a single float.

    Attributes:
        value: The observed numeric value.
    """

    value: float


@dataclass(frozen=True)
class BooleanSensorReading(SensorReading):
    """A sensor reading whose value is a boolean state.

    Attributes:
        value: The observed boolean state.
    """

    value: bool


@dataclass(frozen=True)
class EnumeratedSensorReading(SensorReading):
    """A sensor reading whose value is one of a fixed set of labels.

    Attributes:
        value: The observed label.
    """

    value: str