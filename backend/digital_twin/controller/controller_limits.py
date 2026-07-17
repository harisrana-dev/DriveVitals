"""ControllerLimits: centralized configuration and clamping helpers.

Every numeric bound and smoothing coefficient used anywhere in the
Vehicle Controller layer lives here, as a single injectable
`ControllerLimits` dataclass, plus a small set of pure helper functions
that apply those limits. No controller module hardcodes a threshold or
magic number of its own -- they all take a `ControllerLimits` instance
and call into these helpers.
"""

from __future__ import annotations

from dataclasses import dataclass

from digital_twin.common.exceptions import ConfigurationError


@dataclass(frozen=True)
class ControllerLimits:
    """Bounds and tuning coefficients for the Vehicle Controller layer.

    Attributes:
        max_throttle: Maximum allowed throttle percentage, 0.0 to 1.0.
        max_brake: Maximum allowed brake percentage, 0.0 to 1.0.
        min_steering: Minimum allowed normalized steering value.
        max_steering: Maximum allowed normalized steering value.
        min_gear: Lowest numbered drive gear the transmission supports.
        max_gear: Highest numbered drive gear the transmission supports.
        max_gear_step_per_shift: Maximum number of gear numbers the
            transmission may move in a single shift (prevents skipping
            straight from, e.g., 2nd to 6th gear in one tick).
        min_shift_interval_ticks: Minimum number of ticks that must
            elapse between two gear shifts (prevents gear hunting).
        gear_speed_band_kmh: Width, in km/h, of the speed band assigned
            to each gear when mapping current speed to a target gear
            number (e.g. a value of 20.0 means gear 1 covers 0-20 km/h,
            gear 2 covers 20-40 km/h, and so on).
        stop_speed_threshold_kmh: Speed, in km/h, at or below which the
            vehicle is considered stationary for gear-position
            decisions (PARK/NEUTRAL eligibility).
        throttle_dead_zone: Requested throttle values below this
            magnitude are treated as zero, to avoid actuator chatter.
        brake_dead_zone: Requested brake values below this magnitude
            are treated as zero, to avoid actuator chatter.
        throttle_max_delta_per_tick: Maximum change in throttle
            percentage allowed in a single tick, so throttle changes
            smoothly rather than jumping instantly.
        brake_max_delta_per_tick: Maximum change in brake percentage
            allowed in a single tick under normal (non-emergency)
            braking.
    """

    max_throttle: float = 1.0
    max_brake: float = 1.0
    min_steering: float = -1.0
    max_steering: float = 1.0
    min_gear: int = 1
    max_gear: int = 7
    max_gear_step_per_shift: int = 1
    min_shift_interval_ticks: int = 3
    gear_speed_band_kmh: float = 20.0
    stop_speed_threshold_kmh: float = 2.0
    throttle_dead_zone: float = 0.02
    brake_dead_zone: float = 0.02
    throttle_max_delta_per_tick: float = 0.15
    brake_max_delta_per_tick: float = 0.25

    def __post_init__(self) -> None:
        """Validate that all bounds and coefficients are well-formed.

        Raises:
            ConfigurationError: If any percentage bound is outside
                [0.0, 1.0], steering bounds are inverted, gear bounds
                are inverted or non-positive, or any coefficient is
                negative.
        """
        for percent_field in ("max_throttle", "max_brake"):
            value = getattr(self, percent_field)
            if not (0.0 <= value <= 1.0):
                raise ConfigurationError(f"{percent_field} must be between 0.0 and 1.0.")
        if self.min_steering >= self.max_steering:
            raise ConfigurationError("min_steering must be less than max_steering.")
        if self.min_gear < 1:
            raise ConfigurationError("min_gear must be >= 1.")
        if self.max_gear < self.min_gear:
            raise ConfigurationError("max_gear must be >= min_gear.")
        if self.max_gear_step_per_shift < 1:
            raise ConfigurationError("max_gear_step_per_shift must be >= 1.")
        if self.min_shift_interval_ticks < 0:
            raise ConfigurationError("min_shift_interval_ticks cannot be negative.")
        if self.gear_speed_band_kmh <= 0:
            raise ConfigurationError("gear_speed_band_kmh must be positive.")
        if self.stop_speed_threshold_kmh < 0:
            raise ConfigurationError("stop_speed_threshold_kmh cannot be negative.")
        for dead_zone_field in ("throttle_dead_zone", "brake_dead_zone"):
            if getattr(self, dead_zone_field) < 0:
                raise ConfigurationError(f"{dead_zone_field} cannot be negative.")
        for delta_field in ("throttle_max_delta_per_tick", "brake_max_delta_per_tick"):
            if getattr(self, delta_field) <= 0:
                raise ConfigurationError(f"{delta_field} must be positive.")


def apply_dead_zone(value: float, dead_zone: float) -> float:
    """Zero out a value if its magnitude falls within the dead zone.

    Args:
        value: The raw input value.
        dead_zone: The dead zone half-width around 0.0.

    Returns:
        0.0 if `abs(value) <= dead_zone`, otherwise `value` unchanged.
    """
    return 0.0 if abs(value) <= dead_zone else value


def clamp_throttle(value: float, limits: ControllerLimits) -> float:
    """Clamp a throttle percentage into `[0.0, limits.max_throttle]`.

    Args:
        value: Raw throttle percentage.
        limits: The active ControllerLimits.

    Returns:
        The clamped throttle percentage.
    """
    return min(limits.max_throttle, max(0.0, value))


def clamp_brake(value: float, limits: ControllerLimits) -> float:
    """Clamp a brake percentage into `[0.0, limits.max_brake]`.

    Args:
        value: Raw brake percentage.
        limits: The active ControllerLimits.

    Returns:
        The clamped brake percentage.
    """
    return min(limits.max_brake, max(0.0, value))


def clamp_steering(value: float, limits: ControllerLimits) -> float:
    """Clamp a steering value into `[limits.min_steering, limits.max_steering]`.

    Args:
        value: Raw normalized steering value.
        limits: The active ControllerLimits.

    Returns:
        The clamped steering value.
    """
    return min(limits.max_steering, max(limits.min_steering, value))


def clamp_gear_number(gear_number: int, limits: ControllerLimits) -> int:
    """Clamp a numeric gear into `[limits.min_gear, limits.max_gear]`.

    Args:
        gear_number: Raw target gear number.
        limits: The active ControllerLimits.

    Returns:
        The clamped gear number.
    """
    return min(limits.max_gear, max(limits.min_gear, gear_number))


def rate_limit(previous_value: float, target_value: float, max_delta: float) -> float:
    """Move a value toward a target by at most `max_delta` this tick.

    The core smoothing primitive used by both ThrottleController and
    BrakeController so commanded percentages never jump instantly.

    Args:
        previous_value: The value commanded on the previous tick.
        target_value: The value that would be commanded with no
            smoothing applied.
        max_delta: Maximum allowed change in either direction this
            tick.

    Returns:
        `target_value` if it is within `max_delta` of `previous_value`,
        otherwise `previous_value` moved by `max_delta` toward
        `target_value`.
    """
    delta = target_value - previous_value
    if delta > max_delta:
        return previous_value + max_delta
    if delta < -max_delta:
        return previous_value - max_delta
    return target_value