"""Vehicle entity: domain data describing a single physical vehicle.

Pure data model. The Vehicle owns its state but never updates it --
per the Digital Twin's responsibility rules, a future Physics engine is
solely responsible for mutating `VehicleState` fields (speed, RPM,
fuel level, wear, etc.) tick over tick. This module only defines the
shape of that state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from digital_twin.common.enums import MaintenanceStatus, VehicleStatus
from digital_twin.common.exceptions import ConfigurationError


class FuelType(str, Enum):
    """Fuel/energy type a vehicle uses."""

    GASOLINE = "GASOLINE"
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    CNG = "CNG"


class TransmissionType(str, Enum):
    """Transmission type a vehicle uses."""

    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
    CVT = "CVT"
    SINGLE_SPEED = "SINGLE_SPEED"


@dataclass(frozen=True)
class VehicleSpecification:
    """Static manufacturing specification of a vehicle.

    These values do not change over the vehicle's lifetime in the
    simulation (unlike `VehicleState`, which changes every tick).

    Attributes:
        manufacturer: Vehicle manufacturer name.
        model: Vehicle model name.
        year: Model year.
        fuel_type: Fuel/energy type the vehicle uses.
        transmission: Transmission type the vehicle uses.
    """

    manufacturer: str
    model: str
    year: int
    fuel_type: FuelType
    transmission: TransmissionType

    def __post_init__(self) -> None:
        """Validate the model year is plausible.

        Raises:
            ConfigurationError: If year is before 1900.
        """
        if self.year < 1900:
            raise ConfigurationError("VehicleSpecification.year must be >= 1900.")


@dataclass
class VehicleState:
    """Mutable, persistent operating state of a vehicle.

    Populated and updated exclusively by a future Physics engine; the
    Vehicle entity itself performs no computation on these fields.

    Attributes:
        current_speed_kmh: Current speed, in km/h.
        current_gear: Current gear (0 for neutral/park, negative for
            reverse).
        current_rpm: Current engine RPM.
        fuel_level_percent: Current fuel/battery level, 0.0 to 100.0.
        engine_temperature_celsius: Current engine temperature.
        engine_load_percent: Current engine load, 0.0 to 100.0.
        battery_voltage: Current battery voltage.
        tyre_wear_percent: Cumulative tyre wear, 0.0 (new) to 100.0
            (fully worn).
        brake_wear_percent: Cumulative brake wear, 0.0 (new) to 100.0
            (fully worn).
        engine_health_percent: Overall engine health, 0.0 to 100.0.
        odometer_km: Cumulative distance driven, in kilometers.
        engine_hours: Cumulative hours the engine has run.
        health_score: Overall composite health score, 0.0 to 100.0.
    """

    current_speed_kmh: float = 0.0
    current_gear: int = 0
    current_rpm: float = 0.0
    fuel_level_percent: float = 100.0
    engine_temperature_celsius: float = 20.0
    engine_load_percent: float = 0.0
    battery_voltage: float = 12.6
    tyre_wear_percent: float = 0.0
    brake_wear_percent: float = 0.0
    engine_health_percent: float = 100.0
    odometer_km: float = 0.0
    engine_hours: float = 0.0
    health_score: float = 100.0

    def __post_init__(self) -> None:
        """Validate percentage-bounded fields and non-negative cumulative fields.

        Raises:
            ConfigurationError: If a percentage field is outside
                [0.0, 100.0] or a cumulative field is negative.
        """
        for percent_field in (
            "fuel_level_percent",
            "engine_load_percent",
            "tyre_wear_percent",
            "brake_wear_percent",
            "engine_health_percent",
            "health_score",
        ):
            value = getattr(self, percent_field)
            if not (0.0 <= value <= 100.0):
                raise ConfigurationError(f"{percent_field} must be between 0.0 and 100.0.")
        if self.odometer_km < 0:
            raise ConfigurationError("odometer_km cannot be negative.")
        if self.engine_hours < 0:
            raise ConfigurationError("engine_hours cannot be negative.")


@dataclass
class Vehicle:
    """A single physical vehicle and its persistent domain state.

    Attributes:
        vehicle_id: Unique identifier for the vehicle.
        vin: Vehicle Identification Number.
        specification: Static manufacturing specification.
        current_driver_id: Id of the driver currently assigned, if any.
        current_trip_id: Id of the trip currently assigned, if any.
        current_shift_id: Id of the shift currently assigned, if any.
        current_route_id: Id of the route currently assigned, if any.
        current_cargo_id: Id of the cargo currently loaded, if any.
        status: Current lifecycle/availability status.
        state: Mutable operating state (speed, RPM, wear, etc.).
        maintenance_status: Current maintenance status.
    """

    vehicle_id: str
    vin: str
    specification: VehicleSpecification
    current_driver_id: str | None = None
    current_trip_id: str | None = None
    current_shift_id: str | None = None
    current_route_id: str | None = None
    current_cargo_id: str | None = None
    status: VehicleStatus = VehicleStatus.AVAILABLE
    state: VehicleState = field(default_factory=VehicleState)
    maintenance_status: MaintenanceStatus = MaintenanceStatus.OK

    def __post_init__(self) -> None:
        """Validate the VIN is present.

        Raises:
            ConfigurationError: If vin is empty.
        """
        if not self.vin:
            raise ConfigurationError("Vehicle.vin cannot be empty.")