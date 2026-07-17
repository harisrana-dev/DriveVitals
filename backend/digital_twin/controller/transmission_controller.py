"""TransmissionController: coordinates gear selection and clutch state.

Sits between `GearLogic` (which decides *what gear*) and
`VehicleController` (the top-level orchestrator), deciding whether the
engine is currently coupled to the drivetrain (`clutch_engaged`) given
the requested gear and transmission type. Performs no physics -- it
never computes RPM, acceleration, or torque.
"""

from __future__ import annotations

from dataclasses import dataclass

from digital_twin.controller.controller_limits import ControllerLimits
from digital_twin.controller.gear_logic import GearLogic, GearPosition, RequestedGear
from digital_twin.decision.driver_intent import DriverIntent
from digital_twin.entities.vehicle import TransmissionType, Vehicle


@dataclass(frozen=True)
class TransmissionCommand:
    """The transmission-related portion of a vehicle actuation command.

    Attributes:
        requested_gear: The gear position/number requested this tick.
        clutch_engaged: Whether the engine is coupled to the
            drivetrain this tick.
        reverse_selected: Whether reverse is currently requested;
            always consistent with `requested_gear.position`.
    """

    requested_gear: RequestedGear
    clutch_engaged: bool
    reverse_selected: bool


class TransmissionController:
    """Coordinates gear logic and clutch engagement into one command.

    Depends on `GearLogic` for gear selection, injected so it can be
    swapped or faked independently of clutch-engagement policy.
    """

    def __init__(self, gear_logic: GearLogic | None = None) -> None:
        """Initialize the transmission controller.

        Args:
            gear_logic: Gear selection strategy. Defaults to a new
                `GearLogic`.
        """
        self._gear_logic = gear_logic or GearLogic()

    def compute_actuation(
        self,
        intent: DriverIntent,
        vehicle: Vehicle,
        current_gear: RequestedGear,
        ticks_since_last_shift: int,
        limits: ControllerLimits,
        reverse_requested: bool = False,
    ) -> TransmissionCommand:
        """Compute this tick's transmission command.

        Args:
            intent: The driver's intent for this tick.
            vehicle: The vehicle this command is being computed for;
                used to read current speed and transmission type.
            current_gear: The gear requested on the previous tick.
            ticks_since_last_shift: Ticks elapsed since the
                transmission last changed gear number or position.
            limits: Active ControllerLimits.
            reverse_requested: Whether reverse has been explicitly
                requested (see `GearLogic.determine_gear`).

        Returns:
            The TransmissionCommand for this tick.
        """
        requested_gear = self._gear_logic.determine_gear(
            current_speed_kmh=vehicle.state.current_speed_kmh,
            intent=intent,
            current_gear=current_gear,
            ticks_since_last_shift=ticks_since_last_shift,
            limits=limits,
            reverse_requested=reverse_requested,
        )

        clutch_engaged = self._determine_clutch_engagement(
            requested_gear=requested_gear,
            transmission_type=vehicle.specification.transmission,
            is_shifting=(
                requested_gear.position == GearPosition.DRIVE
                and current_gear.position == GearPosition.DRIVE
                and requested_gear.gear_number != current_gear.gear_number
            ),
        )

        return TransmissionCommand(
            requested_gear=requested_gear,
            clutch_engaged=clutch_engaged,
            reverse_selected=requested_gear.position == GearPosition.REVERSE,
        )

    def _determine_clutch_engagement(
        self,
        requested_gear: RequestedGear,
        transmission_type: TransmissionType,
        is_shifting: bool,
    ) -> bool:
        """Decide whether the engine is coupled to the drivetrain this tick.

        The engine is decoupled (clutch disengaged) whenever the
        transmission is in PARK or NEUTRAL, since no drive gear is
        engaged. For a MANUAL transmission, the clutch is also
        momentarily disengaged during an active gear-number change,
        reflecting a driver depressing the clutch pedal to shift; other
        transmission types (AUTOMATIC, CVT, SINGLE_SPEED) do not
        require this since they can shift without decoupling.

        Args:
            requested_gear: The gear requested this tick.
            transmission_type: The vehicle's transmission type.
            is_shifting: Whether a gear-number change is occurring this
                tick relative to the previous tick.

        Returns:
            True if the engine should be coupled to the drivetrain.
        """
        if requested_gear.position in (GearPosition.PARK, GearPosition.NEUTRAL):
            return False
        if transmission_type == TransmissionType.MANUAL and is_shifting:
            return False
        return True