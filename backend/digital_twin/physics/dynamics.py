"""Dynamics: computes net vehicle acceleration for the current tick.

Combines the drive/brake force implied by `VehicleActuation` with the
resistive forces from `ResistanceModel` to produce a single
acceleration value, in m/s^2, respecting configured clamps and the
current traction limit. Never decides *what* the driver wants (that's
the Decision Layer) or *what command* to send (that's the Vehicle
Controller) -- only how the vehicle physically responds to a command
already given.
"""

from __future__ import annotations

from digital_twin.controller.gear_logic import GearPosition
from digital_twin.controller.vehicle_actuation import VehicleActuation
from digital_twin.physics import physics_constants as const
from digital_twin.physics.resistance_model import ResistanceModel


class Dynamics:
    """Computes net acceleration from actuation, mass, and resistance.

    Depends on `ResistanceModel` for the resistive forces it combines
    with drive/brake force; injected so it can be swapped or faked
    independently.
    """

    def __init__(self, resistance_model: ResistanceModel | None = None) -> None:
        """Initialize the dynamics model.

        Args:
            resistance_model: Source of rolling resistance, drag, and
                traction-limit calculations. Defaults to a new
                `ResistanceModel`.
        """
        self._resistance_model = resistance_model or ResistanceModel()

    def compute_acceleration_mps2(
        self,
        actuation: VehicleActuation,
        current_speed_kmh: float,
        mass_kg: float,
        traction_factor: float,
    ) -> float:
        """Compute this tick's net longitudinal acceleration.

        Args:
            actuation: The commanded throttle/brake/gear/clutch state
                from the Vehicle Controller.
            current_speed_kmh: The vehicle's speed at the start of this
                tick.
            mass_kg: Vehicle mass, in kilograms.
            traction_factor: Traction (grip) multiplier in (0.0, 1.0],
                from `ResistanceModel.compute_traction_factor`, capping
                how much of the commanded drive/brake force can
                actually be delivered.

        Returns:
            Net acceleration, in m/s^2, clamped to
            `[-MAX_DECELERATION_MPS2, MAX_ACCELERATION_MPS2]`. Negative
            values indicate deceleration.
        """
        is_stopped = current_speed_kmh <= const.STOPPED_SPEED_EPSILON_KMH
        powertrain_connected = actuation.clutch_engaged and actuation.requested_gear.position in (
            GearPosition.DRIVE,
            GearPosition.REVERSE,
        )

        drive_force_n = 0.0
        if powertrain_connected:
            drive_force_n = (
                actuation.throttle_percentage
                * const.DEFAULT_MAX_ENGINE_FORCE_N
                * traction_factor
            )

        brake_force_n = (
            actuation.brake_percentage * const.DEFAULT_MAX_BRAKE_FORCE_N * traction_factor
        )

        resistance_force_n = 0.0
        if not is_stopped:
            resistance_force_n = (
                self._resistance_model.compute_rolling_resistance_force_n(mass_kg)
                + self._resistance_model.compute_aerodynamic_drag_force_n(current_speed_kmh)
            )

        engine_braking_force_n = 0.0
        if (
            powertrain_connected
            and not is_stopped
            and actuation.throttle_percentage <= 0.0
            and actuation.brake_percentage <= 0.0
        ):
            engine_braking_force_n = const.ENGINE_BRAKING_DECELERATION_MPS2 * mass_kg

        net_force_n = (
            drive_force_n - brake_force_n - resistance_force_n - engine_braking_force_n
        )

        acceleration_mps2 = net_force_n / mass_kg
        return max(
            -const.MAX_DECELERATION_MPS2,
            min(const.MAX_ACCELERATION_MPS2, acceleration_mps2),
        )