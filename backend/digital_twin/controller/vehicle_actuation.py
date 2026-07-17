"""VehicleActuation: the sole output type produced by the Vehicle Controller.

A `VehicleActuation` describes the commands an ECU-like controller
would send to a vehicle's actuators. It never describes the vehicle's
resulting physical state -- speed, RPM, acceleration, fuel, and wear
belong exclusively to `digital_twin.entities.vehicle.VehicleState`,
which only a future Physics Engine may write to. The Vehicle
Controller reads `Vehicle`/`VehicleSpecification` and a `DriverIntent`
but never mutates either; this dataclass is its only output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.controller.gear_logic import GearPosition, RequestedGear


@dataclass(frozen=True)
class VehicleActuation:
    """An immutable statement of vehicle actuator commands for the current tick.

    Consumed downstream by a future Physics Engine, which decides
    whether/how well the vehicle actually achieves these commands
    (traction, engine performance, road conditions, etc.). This module
    and its producer (the Vehicle Controller) never touch
    `VehicleState` directly.

    Attributes:
        throttle_percentage: Normalized throttle command, 0.0 to 1.0.
        brake_percentage: Normalized brake command, 0.0 to 1.0.
        requested_gear: The transmission position/gear being requested.
        steering_angle: Normalized steering command, -1.0 (full left)
            to 1.0 (full right); 0.0 means "hold straight".
        clutch_engaged: Whether the clutch (or, for automatics, the
            torque-converter/lockup analog) is engaged, coupling the
            engine to the drivetrain.
        engine_enabled: Whether the engine is commanded to run.
        parking_brake: Whether the parking brake is commanded engaged.
        reverse_selected: Whether reverse gear is currently requested;
            always consistent with `requested_gear.position`.
        cruise_control_enabled: Whether the controller is operating in
            a speed-holding (cruise) mode for this tick.
        controller_reason: Human-readable explanation of the dominant
            factor(s) behind this actuation command, useful for
            logging/debugging.
        timestamp: Simulated time at which this actuation was computed.
    """

    throttle_percentage: float
    brake_percentage: float
    requested_gear: RequestedGear
    steering_angle: float
    clutch_engaged: bool
    engine_enabled: bool
    parking_brake: bool
    reverse_selected: bool
    cruise_control_enabled: bool
    controller_reason: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate normalized fields and cross-field consistency.

        Raises:
            ConfigurationError: If throttle/brake/steering fall outside
                their valid ranges, throttle and brake are both
                positive, or `reverse_selected`/`parking_brake` are
                inconsistent with `requested_gear.position`.
        """
        if not (0.0 <= self.throttle_percentage <= 1.0):
            raise ConfigurationError("throttle_percentage must be between 0.0 and 1.0.")
        if not (0.0 <= self.brake_percentage <= 1.0):
            raise ConfigurationError("brake_percentage must be between 0.0 and 1.0.")
        if not (-1.0 <= self.steering_angle <= 1.0):
            raise ConfigurationError("steering_angle must be between -1.0 and 1.0.")
        if self.throttle_percentage > 0.0 and self.brake_percentage > 0.0:
            raise ConfigurationError(
                "throttle_percentage and brake_percentage cannot both be positive."
            )
        if self.reverse_selected != (self.requested_gear.position == GearPosition.REVERSE):
            raise ConfigurationError(
                "reverse_selected must match requested_gear.position == REVERSE."
            )
        if self.parking_brake and self.requested_gear.position != GearPosition.PARK:
            raise ConfigurationError(
                "parking_brake cannot be engaged unless requested_gear.position is PARK."
            )