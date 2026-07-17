"""VehicleController: orchestrator for the Vehicle Controller layer.

Reads a `DriverIntent` plus the `Vehicle` it applies to, and produces a
single `VehicleActuation`. This is the pipeline stage positioned after
the Driver Behaviour Engine and before the (future) Physics Engine. It
never mutates `Vehicle`/`VehicleState`, never computes vehicle motion,
and never generates telemetry -- it only decides what commands to send.
"""

from __future__ import annotations

from digital_twin.controller.brake_controller import BrakeController
from digital_twin.controller.controller_limits import ControllerLimits, clamp_steering
from digital_twin.controller.gear_logic import (
    DEFAULT_INITIAL_GEAR,
    GearLogic,
    GearPosition,
    RequestedGear,
)
from digital_twin.controller.throttle_controller import ThrottleController
from digital_twin.controller.transmission_controller import TransmissionController
from digital_twin.controller.vehicle_actuation import VehicleActuation
from digital_twin.decision.driver_intent import DriverIntent
from digital_twin.entities.vehicle import Vehicle
from digital_twin.runtime.tick_context import TickContext


class VehicleController:
    """Translates a DriverIntent into a VehicleActuation for one vehicle.

    Depends on `ThrottleController`, `BrakeController`, and
    `TransmissionController` (each independently injectable), plus a
    `ControllerLimits` instance shared by all three so every clamp and
    smoothing coefficient in the pipeline comes from one configuration
    object.
    """

    def __init__(
        self,
        limits: ControllerLimits | None = None,
        throttle_controller: ThrottleController | None = None,
        brake_controller: BrakeController | None = None,
        transmission_controller: TransmissionController | None = None,
    ) -> None:
        """Initialize the controller, defaulting to the standard component set.

        Args:
            limits: Shared ControllerLimits. Defaults to a new
                `ControllerLimits` with standard bounds.
            throttle_controller: Throttle command computer. Defaults
                to a new `ThrottleController`.
            brake_controller: Brake command computer. Defaults to a
                new `BrakeController`.
            transmission_controller: Gear/clutch command computer.
                Defaults to a new `TransmissionController`.
        """
        self._limits = limits or ControllerLimits()
        self._throttle_controller = throttle_controller or ThrottleController()
        self._brake_controller = brake_controller or BrakeController()
        self._transmission_controller = transmission_controller or TransmissionController(
            gear_logic=GearLogic()
        )

    def compute_actuation(
        self,
        intent: DriverIntent,
        vehicle: Vehicle,
        tick_context: TickContext,
        previous_actuation: VehicleActuation | None = None,
        ticks_since_last_shift: int = 0,
        reverse_requested: bool = False,
    ) -> VehicleActuation:
        """Compute this tick's VehicleActuation for the given vehicle.

        Args:
            intent: The driver's intent for this tick, produced by the
                Driver Behaviour Engine.
            vehicle: The vehicle this actuation applies to. Read only
                -- never mutated.
            tick_context: The simulation's immutable per-tick context,
                used to timestamp the resulting actuation.
            previous_actuation: The actuation computed on the previous
                tick for this vehicle, if any. Supplies the throttle,
                brake, and gear baselines that smoothing and shift
                protection are measured against; `None` is treated as
                "vehicle starting from PARK with throttle/brake at 0",
                appropriate for the first tick a vehicle is actuated.
            ticks_since_last_shift: Number of ticks elapsed since the
                transmission last changed gear number or position.
                Callers that track this across ticks should pass the
                real value; the default of 0 means "just shifted",
                which conservatively blocks an immediate second shift
                until `limits.min_shift_interval_ticks` has elapsed.
            reverse_requested: Whether reverse has been explicitly
                requested (see `GearLogic.determine_gear`).

        Returns:
            The resulting VehicleActuation. `vehicle` and `intent` are
            never mutated.
        """
        previous_gear = previous_actuation.requested_gear if previous_actuation else (
            DEFAULT_INITIAL_GEAR
        )
        previous_throttle = (
            previous_actuation.throttle_percentage if previous_actuation else 0.0
        )
        previous_brake = previous_actuation.brake_percentage if previous_actuation else 0.0

        transmission_command = self._transmission_controller.compute_actuation(
            intent=intent,
            vehicle=vehicle,
            current_gear=previous_gear,
            ticks_since_last_shift=ticks_since_last_shift,
            limits=self._limits,
            reverse_requested=reverse_requested,
        )

        brake_percentage = self._brake_controller.compute_brake(
            intent=intent,
            previous_brake=previous_brake,
            limits=self._limits,
        )

        if brake_percentage > 0.0:
            throttle_percentage = 0.0
        else:
            throttle_percentage = self._throttle_controller.compute_throttle(
                intent=intent,
                vehicle=vehicle,
                specification=vehicle.specification,
                previous_throttle=previous_throttle,
                limits=self._limits,
            )

        steering_angle = clamp_steering(intent.steering_request, self._limits)

        requested_gear = transmission_command.requested_gear
        parking_brake = requested_gear.position == GearPosition.PARK
        cruise_control_enabled = self._is_cruise_control_active(intent, requested_gear)

        return VehicleActuation(
            throttle_percentage=throttle_percentage,
            brake_percentage=brake_percentage,
            requested_gear=requested_gear,
            steering_angle=steering_angle,
            clutch_engaged=transmission_command.clutch_engaged,
            engine_enabled=True,
            parking_brake=parking_brake,
            reverse_selected=transmission_command.reverse_selected,
            cruise_control_enabled=cruise_control_enabled,
            controller_reason=self._explain(intent, requested_gear, brake_percentage),
            timestamp=tick_context.simulation_time,
        )

    def _is_cruise_control_active(
        self, intent: DriverIntent, requested_gear: RequestedGear
    ) -> bool:
        """Determine whether cruise control is active this tick.

        Args:
            intent: The driver's intent for this tick.
            requested_gear: The gear requested this tick.

        Returns:
            True if the vehicle is in DRIVE and the driver is not
            requesting a stop, emergency stop, or overtake -- i.e. a
            steady cruising state.
        """
        return (
            requested_gear.position == GearPosition.DRIVE
            and not intent.request_stop
            and not intent.request_emergency_stop
            and not intent.overtake_requested
        )

    def _explain(
        self,
        intent: DriverIntent,
        requested_gear: RequestedGear,
        brake_percentage: float,
    ) -> str:
        """Build a concise, human-readable explanation for this actuation.

        Args:
            intent: The driver's intent for this tick.
            requested_gear: The gear requested this tick.
            brake_percentage: The computed brake command.

        Returns:
            A short string naming the dominant factor(s) behind the
            computed actuation.
        """
        if intent.request_emergency_stop:
            return "Emergency stop: full brake, throttle inhibited."
        if requested_gear.position == GearPosition.PARK:
            return "Vehicle stationary and stopped: transmission in PARK."
        if requested_gear.position == GearPosition.NEUTRAL:
            return "Vehicle stationary, no drive intent: transmission in NEUTRAL."
        if brake_percentage > 0.0:
            return f"Braking toward target speed {intent.target_speed_kmh:.1f} km/h."
        return f"Driving toward target speed {intent.target_speed_kmh:.1f} km/h."