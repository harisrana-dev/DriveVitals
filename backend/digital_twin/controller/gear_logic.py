"""GearLogic: deterministic gear selection for the Vehicle Controller.

Decides which gear position and, where applicable, which numbered gear
the transmission should request. Never computes RPM or acceleration --
those are strictly the Physics Engine's responsibility. This module
only decides *what gear is requested*; whether the vehicle can actually
achieve that gear is decided downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.controller.controller_limits import ControllerLimits, clamp_gear_number
from digital_twin.decision.driver_intent import DriverIntent


class GearPosition(str, Enum):
    """Transmission position, independent of transmission type.

    `DRIVE` covers both automatic "D" and any manual forward gear;
    `gear_number` on `RequestedGear` distinguishes which forward gear
    is actually engaged. This keeps one gear model usable for
    automatic, manual, and (per the brief's future-extension note) CVT
    or heavy-truck transmissions without a parallel type hierarchy.
    """

    PARK = "PARK"
    REVERSE = "REVERSE"
    NEUTRAL = "NEUTRAL"
    DRIVE = "DRIVE"


@dataclass(frozen=True)
class RequestedGear:
    """A single, immutable gear request.

    Attributes:
        position: The transmission position being requested.
        gear_number: The numbered forward gear (1-7 by default range,
            per `ControllerLimits.min_gear`/`max_gear`) engaged while
            in `DRIVE`. Always `None` for PARK, REVERSE, and NEUTRAL.
    """

    position: GearPosition
    gear_number: int | None = None

    def __post_init__(self) -> None:
        """Validate that gear_number is present only for DRIVE.

        Raises:
            ConfigurationError: If gear_number is set while position
                is not DRIVE, or is missing while position is DRIVE.
        """
        if self.position == GearPosition.DRIVE and self.gear_number is None:
            raise ConfigurationError("gear_number is required when position is DRIVE.")
        if self.position != GearPosition.DRIVE and self.gear_number is not None:
            raise ConfigurationError("gear_number must be None unless position is DRIVE.")


#: The default, parked/stationary gear request, used when no prior
#: actuation exists yet (e.g. the very first tick for a vehicle).
DEFAULT_INITIAL_GEAR: RequestedGear = RequestedGear(position=GearPosition.PARK)


class GearLogic:
    """Determines the transmission's requested gear for the current tick.

    Stateless: `determine_gear` is a pure function of its arguments.
    Callers are responsible for tracking `ticks_since_last_shift`
    across ticks (typically by comparing the previous and newly
    returned `RequestedGear`), since this class holds no state of its
    own.
    """

    def determine_gear(
        self,
        current_speed_kmh: float,
        intent: DriverIntent,
        current_gear: RequestedGear,
        ticks_since_last_shift: int,
        limits: ControllerLimits,
        reverse_requested: bool = False,
    ) -> RequestedGear:
        """Compute the gear request for this tick.

        Args:
            current_speed_kmh: The vehicle's current speed.
            intent: The driver's intent for this tick.
            current_gear: The gear requested on the previous tick.
            ticks_since_last_shift: Number of ticks elapsed since the
                transmission last changed gear number or position.
            limits: Active ControllerLimits (gear bounds, shift
                interval, speed-to-gear band, stop threshold).
            reverse_requested: Whether reverse has been explicitly
                requested. The current Decision Layer never sets this
                (it has no reverse concept yet); the parameter exists
                so GearLogic already supports reverse for a future
                sprint without changing this method's signature.

        Returns:
            The RequestedGear for this tick.
        """
        is_stationary = current_speed_kmh <= limits.stop_speed_threshold_kmh

        if reverse_requested and is_stationary:
            return RequestedGear(position=GearPosition.REVERSE)

        if is_stationary and intent.request_stop and not intent.request_emergency_stop:
            return RequestedGear(position=GearPosition.PARK)

        if is_stationary and intent.target_speed_kmh <= 0.0:
            return RequestedGear(position=GearPosition.NEUTRAL)

        target_gear_number = self._select_gear_number_for_speed(current_speed_kmh, limits)
        resolved_gear_number = self._apply_shift_protection(
            current_gear=current_gear,
            target_gear_number=target_gear_number,
            ticks_since_last_shift=ticks_since_last_shift,
            limits=limits,
        )
        return RequestedGear(position=GearPosition.DRIVE, gear_number=resolved_gear_number)

    def _select_gear_number_for_speed(
        self, current_speed_kmh: float, limits: ControllerLimits
    ) -> int:
        """Map current speed to the gear number that would suit it.

        Args:
            current_speed_kmh: The vehicle's current speed.
            limits: Active ControllerLimits.

        Returns:
            A gear number within `[limits.min_gear, limits.max_gear]`.
        """
        raw_gear = limits.min_gear + int(current_speed_kmh // limits.gear_speed_band_kmh)
        return clamp_gear_number(raw_gear, limits)

    def _apply_shift_protection(
        self,
        current_gear: RequestedGear,
        target_gear_number: int,
        ticks_since_last_shift: int,
        limits: ControllerLimits,
    ) -> int:
        """Prevent gear hunting and enforce minimum shift interval/step size.

        Args:
            current_gear: The gear requested on the previous tick.
            target_gear_number: The gear number speed alone would
                select.
            ticks_since_last_shift: Ticks elapsed since the last shift.
            limits: Active ControllerLimits.

        Returns:
            The gear number to actually request this tick: either the
            unchanged current gear number (if not enough time has
            elapsed since the last shift), or the target gear number
            moved toward by at most `max_gear_step_per_shift`.
        """
        # No prior DRIVE gear to compare against (e.g. just left PARK):
        # engage directly at the speed-appropriate gear.
        if current_gear.position != GearPosition.DRIVE or current_gear.gear_number is None:
            return target_gear_number

        if target_gear_number == current_gear.gear_number:
            return current_gear.gear_number

        if ticks_since_last_shift < limits.min_shift_interval_ticks:
            return current_gear.gear_number

        step = max(-limits.max_gear_step_per_shift, min(
            limits.max_gear_step_per_shift, target_gear_number - current_gear.gear_number
        ))
        return clamp_gear_number(current_gear.gear_number + step, limits)