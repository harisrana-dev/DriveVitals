"""DriverIntent: the sole output type produced by the Decision Layer.

A `DriverIntent` describes what a driver *wants* the vehicle to do. It
never describes what the vehicle *is currently doing* -- fields like
speed, RPM, gear, engine load, and fuel level belong exclusively to
`digital_twin.entities.vehicle.VehicleState`, which only a future
Physics Engine may write to. The Decision Layer reads vehicle/driver
state but never mutates it; `DriverIntent` is its only output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from digital_twin.common.exceptions import ConfigurationError


@dataclass(frozen=True)
class DriverIntent:
    """An immutable statement of driver intent for the current tick.

    Consumed downstream by a future Vehicle Controller, which is
    responsible for translating intent into actuator commands that the
    Physics Engine then applies to `VehicleState`. This module and its
    producers (the Decision Layer) never touch `VehicleState` directly.

    Attributes:
        target_speed_kmh: Speed the driver wants the vehicle to reach
            or maintain.
        desired_acceleration_mps2: Desired longitudinal acceleration,
            in meters per second squared. Positive values indicate a
            desire to speed up, negative values a desire to slow down.
        throttle_request: Normalized throttle request, 0.0 (none) to
            1.0 (full throttle).
        brake_request: Normalized brake request, 0.0 (none) to 1.0
            (full braking).
        steering_request: Normalized lateral steering intent, -1.0
            (full left) to 1.0 (full right); 0.0 means "hold lane".
        request_stop: Whether the driver intends to bring the vehicle
            to a controlled stop (e.g. end of route, road closure).
        request_emergency_stop: Whether the driver intends an
            emergency stop (e.g. hazard directly ahead).
        request_lane_change: Whether the driver intends to change
            lanes (direction implied by `steering_request`).
        overtake_requested: Whether the driver intends to overtake a
            slower vehicle ahead.
        reason: Human-readable explanation of the dominant factor(s)
            behind this intent, useful for logging/debugging and for
            a future Analytics layer to explain driver behavior.
        decision_timestamp: Simulated time at which this intent was
            produced.
    """

    target_speed_kmh: float
    desired_acceleration_mps2: float
    throttle_request: float
    brake_request: float
    steering_request: float
    request_stop: bool
    request_emergency_stop: bool
    request_lane_change: bool
    overtake_requested: bool
    reason: str
    decision_timestamp: datetime

    def __post_init__(self) -> None:
        """Validate that normalized fields stay within their defined bounds.

        Raises:
            ConfigurationError: If target_speed_kmh is negative, or any
                normalized request field falls outside its valid range.
        """
        if self.target_speed_kmh < 0:
            raise ConfigurationError("target_speed_kmh cannot be negative.")
        if not (0.0 <= self.throttle_request <= 1.0):
            raise ConfigurationError("throttle_request must be between 0.0 and 1.0.")
        if not (0.0 <= self.brake_request <= 1.0):
            raise ConfigurationError("brake_request must be between 0.0 and 1.0.")
        if not (-1.0 <= self.steering_request <= 1.0):
            raise ConfigurationError("steering_request must be between -1.0 and 1.0.")
        if self.throttle_request > 0.0 and self.brake_request > 0.0:
            raise ConfigurationError(
                "throttle_request and brake_request cannot both be positive."
            )