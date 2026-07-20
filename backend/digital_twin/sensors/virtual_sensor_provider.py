"""Concrete virtual sensors and VirtualSensorProvider.

===========================================================================
SENSOR SCOPE REPORT (per instructions: report gaps, never fabricate)
===========================================================================

The brief requested 16 sensors. `digital_twin.entities.vehicle.VehicleState`
(frozen for this sprint, not modified) was inspected field-by-field
before writing any sensor. Only 10 of the 16 have a real, direct
`VehicleState` source and are implemented below. The other 6 are
reported here as integration gaps -- no sensor class exists for them,
and `VirtualSensorProvider` never produces a reading (valid or
otherwise) for a signal it can't actually observe.

IMPLEMENTED (10) -- backed by a real VehicleState field:
    Requested name      | VehicleState field                           | Sensor class
    ---------------------|-----------------------------------------------|---------------------------
    Vehicle Speed         | current_speed_kmh                             | VehicleSpeedSensor
    Engine RPM             | current_rpm                                    | EngineRPMSensor
    Gear Position           | current_gear                                    | GearPositionSensor
    Fuel Level              | fuel_level_percent                               | FuelLevelSensor
    Engine Load              | engine_load_percent                               | EngineLoadSensor
    Engine Temperature        | engine_temperature_celsius                         | EngineTemperatureSensor
    Battery Voltage           | battery_voltage                                     | BatteryVoltageSensor
    Odometer                  | odometer_km                                          | OdometerSensor
    Brake Pad Health            | brake_wear_percent (complement: 100 - wear)          | BrakePadHealthSensor
    Tyre Health                  | tyre_wear_percent (complement: 100 - wear)            | TyreHealthSensor

    The two "*Health" sensors report the complement of an existing wear
    field (health = 100 - wear). This is a unit/framing conversion of a
    single real, already-persisted measurement -- not a fabricated
    value and not a derivation requiring any other input.

NOT IMPLEMENTED (6) -- reported as integration gaps, no sensor class exists:
    Throttle Position -- lives on `VehicleActuation.throttle_percentage`
        (a Vehicle Controller *command*), not on `VehicleState`, and is
        not reachable from `Sensor.read(vehicle, state, tick_context)`
        regardless. A real throttle-position sensor observes actual
        throttle plate angle, which VehicleState does not model.
    Brake Position -- same issue as Throttle Position
        (`VehicleActuation.brake_percentage`).
    Fuel Rate -- `VehicleState` persists only cumulative
        `fuel_level_percent`; no instantaneous consumption-rate field
        exists to observe.
    Coolant Temperature -- `VehicleState` has a single
        `engine_temperature_celsius` field, not a distinct coolant
        field. Duplicating that one field under a second sensor
        identity would fabricate a signal that doesn't actually exist
        as separate data, so no CoolantTemperatureSensor is provided.
    Oil Life -- no field on `VehicleState` at all.
    Distance Travelled (as distinct from Odometer) -- `VehicleState`
        only persists the cumulative `odometer_km`; a per-tick "distance
        travelled" would require computing a delta across two
        observations, which is a calculation, not an observation, and
        conflicts with "sensors only observe, no calculations."
        `OdometerSensor` (cumulative distance) is implemented instead.

Recommended fix for a future sprint (not applied here, per instructions
to leave frozen modules untouched): extend `VehicleState` with
`throttle_position_percent`, `brake_position_percent`,
`fuel_rate_l_per_hour`, `coolant_temperature_celsius` (distinct from
engine metal temperature), and `oil_life_percent`; a "distance this
tick" sensor becomes possible once `PhysicsTickResult` (already
computes it) is threaded into the sensor pipeline, or once
`VehicleState` gains its own per-tick distance field.
"""

from __future__ import annotations

from digital_twin.entities.vehicle import Vehicle, VehicleState
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors import sensor_constants as const
from digital_twin.sensors.pid_mapper import PidMetadata, get_pid_metadata
from digital_twin.sensors.sensor_models import NumericSensorReading, SensorReading
from digital_twin.sensors.sensor_provider import Sensor
from digital_twin.sensors.sensor_registry import SensorRegistry


class _NumericVehicleStateSensor(Sensor):
    """Shared base for sensors that read one numeric VehicleState attribute.

    Not part of the public sensor API -- concrete sensors below extend
    this purely to avoid duplicating the "read one attribute, wrap it
    in a NumericSensorReading" pattern several times over. Each
    subclass is still independently instantiable and testable; this
    only removes boilerplate, not behavior.
    """

    _sensor_name: str
    _unit: str
    _state_attribute: str

    @property
    def sensor_name(self) -> str:
        """str: This sensor's unique, stable name."""
        return self._sensor_name

    @property
    def unit(self) -> str:
        """str: Unit of measurement for this sensor's readings."""
        return self._unit

    @property
    def pid(self) -> PidMetadata | None:
        """PidMetadata | None: PID metadata for this sensor, if mapped."""
        return get_pid_metadata(self._sensor_name)

    def read(
        self, vehicle: Vehicle, state: VehicleState, tick_context: TickContext
    ) -> SensorReading:
        """Read this sensor's mapped VehicleState attribute directly.

        Args:
            vehicle: The vehicle being observed. Unused by this base
                implementation (present for interface consistency and
                for any future subclass that needs it).
            state: The vehicle's current state.
            tick_context: The simulation's immutable per-tick context.

        Returns:
            A NumericSensorReading wrapping the observed value. Always
            `valid=True`: every sensor in this module has a confirmed,
            real VehicleState source (see the module-level gap report).
        """
        del vehicle  # Unused by the direct-attribute-read base case.
        value = self._extract_value(state)
        return NumericSensorReading(
            sensor_name=self._sensor_name,
            timestamp=tick_context.simulation_time,
            unit=self._unit,
            pid=self.pid,
            valid=True,
            value=value,
        )

    def _extract_value(self, state: VehicleState) -> float:
        """Extract this sensor's value from VehicleState.

        Default implementation reads `self._state_attribute` directly
        off `state`. Subclasses reporting a derived-but-not-fabricated
        value (e.g. wear -> health complement) override this.

        Args:
            state: The vehicle's current state.

        Returns:
            The observed (or directly complemented) numeric value.
        """
        return float(getattr(state, self._state_attribute))


class VehicleSpeedSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.current_speed_kmh` directly."""

    _sensor_name = "vehicle_speed"
    _unit = const.UNIT_KMH
    _state_attribute = "current_speed_kmh"


class EngineRPMSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.current_rpm` directly."""

    _sensor_name = "engine_rpm"
    _unit = const.UNIT_RPM
    _state_attribute = "current_rpm"


class GearPositionSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.current_gear` directly.

    Reported as a raw number (0=neutral/park, negative=reverse,
    positive=forward gear), matching `current_gear`'s own documented
    convention exactly. A categorical PARK/NEUTRAL/DRIVE label is not
    produced: the persisted field collapses PARK and NEUTRAL to the
    same value (0), so labeling one as "PARK" or "NEUTRAL" would be
    fabricating a distinction the data does not actually support.
    """

    _sensor_name = "gear_position"
    _unit = const.UNIT_GEAR
    _state_attribute = "current_gear"


class FuelLevelSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.fuel_level_percent` directly."""

    _sensor_name = "fuel_level"
    _unit = const.UNIT_PERCENT
    _state_attribute = "fuel_level_percent"


class EngineLoadSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.engine_load_percent` directly."""

    _sensor_name = "engine_load"
    _unit = const.UNIT_PERCENT
    _state_attribute = "engine_load_percent"


class EngineTemperatureSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.engine_temperature_celsius` directly.

    See the module-level gap report: there is no distinct
    `coolant_temperature` field, so no separate
    CoolantTemperatureSensor is provided alongside this one.
    """

    _sensor_name = "engine_temperature"
    _unit = const.UNIT_CELSIUS
    _state_attribute = "engine_temperature_celsius"


class BatteryVoltageSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.battery_voltage` directly."""

    _sensor_name = "battery_voltage"
    _unit = const.UNIT_VOLTS
    _state_attribute = "battery_voltage"


class OdometerSensor(_NumericVehicleStateSensor):
    """Reads `VehicleState.odometer_km` directly.

    This is the cumulative-distance sensor. See the module-level gap
    report for why a separate "distance travelled this tick" sensor
    is not provided.
    """

    _sensor_name = "odometer"
    _unit = const.UNIT_KM
    _state_attribute = "odometer_km"


class BrakePadHealthSensor(_NumericVehicleStateSensor):
    """Reports brake pad health as the complement of `brake_wear_percent`.

    `health = 100.0 - brake_wear_percent`: a direct unit/framing
    conversion of the one real, persisted wear measurement, not a
    fabricated second signal.
    """

    _sensor_name = "brake_pad_health"
    _unit = const.UNIT_PERCENT
    _state_attribute = "brake_wear_percent"

    def _extract_value(self, state: VehicleState) -> float:
        """Return 100 minus the persisted brake wear percentage.

        Args:
            state: The vehicle's current state.

        Returns:
            Brake pad health, 0.0 (fully worn) to 100.0 (new).
        """
        return 100.0 - state.brake_wear_percent


class TyreHealthSensor(_NumericVehicleStateSensor):
    """Reports tyre health as the complement of `tyre_wear_percent`.

    `health = 100.0 - tyre_wear_percent`: a direct unit/framing
    conversion of the one real, persisted wear measurement, not a
    fabricated second signal.
    """

    _sensor_name = "tyre_health"
    _unit = const.UNIT_PERCENT
    _state_attribute = "tyre_wear_percent"

    def _extract_value(self, state: VehicleState) -> float:
        """Return 100 minus the persisted tyre wear percentage.

        Args:
            state: The vehicle's current state.

        Returns:
            Tyre health, 0.0 (fully worn) to 100.0 (new).
        """
        return 100.0 - state.tyre_wear_percent


#: The complete, fixed set of sensors this sprint implements. Order
#: matches the "IMPLEMENTED" table in the module gap report above.
_ALL_SENSOR_TYPES: tuple[type[Sensor], ...] = (
    VehicleSpeedSensor,
    EngineRPMSensor,
    GearPositionSensor,
    FuelLevelSensor,
    EngineLoadSensor,
    EngineTemperatureSensor,
    BatteryVoltageSensor,
    OdometerSensor,
    BrakePadHealthSensor,
    TyreHealthSensor,
)


class VirtualSensorProvider:
    """Owns all virtual sensors and reads them every simulation tick.

    Implements the `SensorProvider` Protocol from `sensor_provider.py`.
    Owns a `SensorRegistry` (injected, not a singleton) holding one
    instance of each sensor in `_ALL_SENSOR_TYPES`. Knows nothing about
    telemetry formatting -- `update_all` returns raw `SensorReading`
    instances only.
    """

    def __init__(self, registry: SensorRegistry | None = None) -> None:
        """Initialize the provider and register the standard sensor set.

        Args:
            registry: The SensorRegistry to use. Defaults to a new,
                empty registry populated with one instance of each
                sensor in `_ALL_SENSOR_TYPES`. Passing a pre-populated
                registry is supported for testing with a reduced or
                fake sensor set.
        """
        if registry is not None:
            self._registry = registry
        else:
            self._registry = SensorRegistry()
            for sensor_type in _ALL_SENSOR_TYPES:
                self._registry.register(sensor_type())

    @property
    def registry(self) -> SensorRegistry:
        """SensorRegistry: The registry of sensors this provider owns."""
        return self._registry

    def update_all(
        self, vehicle: Vehicle, tick_context: TickContext
    ) -> list[SensorReading]:
        """Read every registered sensor for the current tick.

        Args:
            vehicle: The vehicle to observe. Neither `vehicle` nor
                `vehicle.state` is mutated.
            tick_context: The simulation's immutable per-tick context.

        Returns:
            One SensorReading per registered sensor, in registration
            order.
        """
        return [
            sensor.read(vehicle, vehicle.state, tick_context)
            for sensor in self._registry
        ]