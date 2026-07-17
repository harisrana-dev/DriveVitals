"""Powertrain: engine RPM, engine load, idle behavior, gear confirmation.

Never computes acceleration or vehicle motion (Dynamics/Kinematics'
responsibility) -- only the engine-side state that results from the
current speed, gear, and actuation.
"""

from __future__ import annotations

from digital_twin.controller.gear_logic import GearPosition, RequestedGear
from digital_twin.physics import physics_constants as const


class Powertrain:
    """Computes RPM, engine load, and confirmed gear encoding.

    Stateless: every method is a pure function of its arguments. RPM
    smoothing uses the previous tick's RPM (supplied by the caller) so
    this class holds no state of its own.
    """

    def confirm_gear(self, requested_gear: RequestedGear) -> int:
        """Encode a RequestedGear into VehicleState's `current_gear` convention.

        `VehicleState.current_gear` is documented as "0 for
        neutral/park, negative for reverse" with positive integers for
        forward gears -- this method is the single place that encoding
        is applied, so Dynamics/PhysicsEngine never need to know the
        convention themselves.

        Args:
            requested_gear: The gear requested by the Vehicle
                Controller this tick.

        Returns:
            0 for PARK or NEUTRAL, -1 for REVERSE, or the positive
            forward gear number for DRIVE.
        """
        if requested_gear.position in (GearPosition.PARK, GearPosition.NEUTRAL):
            return 0
        if requested_gear.position == GearPosition.REVERSE:
            return -1
        assert requested_gear.gear_number is not None  # Guaranteed by RequestedGear.
        return requested_gear.gear_number

    def compute_target_rpm(
        self,
        current_speed_kmh: float,
        requested_gear: RequestedGear,
        clutch_engaged: bool,
        throttle_percentage: float,
    ) -> float:
        """Compute the RPM the engine is heading toward this tick.

        Args:
            current_speed_kmh: The vehicle's current speed.
            requested_gear: The gear requested this tick.
            clutch_engaged: Whether the engine is coupled to the
                drivetrain this tick.
            throttle_percentage: Commanded throttle, 0.0 to 1.0; adds a
                small "engine flare" contribution so throttle input is
                visible in RPM even before road speed changes.

        Returns:
            Target RPM, clamped to `[IDLE_RPM, MAX_RPM]`.
        """
        if not clutch_engaged or requested_gear.position in (
            GearPosition.PARK,
            GearPosition.NEUTRAL,
        ):
            flare = throttle_percentage * (const.MAX_RPM - const.IDLE_RPM) * 0.15
            return min(const.MAX_RPM, const.IDLE_RPM + flare)

        gear_number = requested_gear.gear_number or 1
        rpm_per_kmh = const.GEAR_RPM_PER_KMH.get(
            gear_number, const.GEAR_RPM_PER_KMH[max(const.GEAR_RPM_PER_KMH)]
        )
        speed_driven_rpm = const.IDLE_RPM + current_speed_kmh * rpm_per_kmh
        flare = throttle_percentage * (const.MAX_RPM - const.IDLE_RPM) * 0.05

        target_rpm = speed_driven_rpm + flare
        return max(const.IDLE_RPM, min(const.MAX_RPM, target_rpm))

    def update_rpm(
        self,
        current_rpm: float,
        target_rpm: float,
        delta_time_seconds: float,
    ) -> float:
        """Move RPM toward its target, respecting the maximum rate of change.

        Args:
            current_rpm: RPM at the start of this tick.
            target_rpm: RPM the engine is heading toward this tick, from
                `compute_target_rpm`.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            The new RPM, clamped to `[IDLE_RPM, MAX_RPM]` and never
            changing by more than
            `MAX_RPM_DELTA_PER_SECOND * delta_time_seconds` from
            `current_rpm` -- this is what prevents unrealistic
            instantaneous RPM jumps.
        """
        max_delta = const.MAX_RPM_DELTA_PER_SECOND * delta_time_seconds
        delta = target_rpm - current_rpm
        if delta > max_delta:
            new_rpm = current_rpm + max_delta
        elif delta < -max_delta:
            new_rpm = current_rpm - max_delta
        else:
            new_rpm = target_rpm
        return max(const.IDLE_RPM, min(const.MAX_RPM, new_rpm))

    def compute_engine_load_percent(
        self,
        throttle_percentage: float,
        current_rpm: float,
    ) -> float:
        """Compute engine load as a function of throttle and RPM.

        Args:
            throttle_percentage: Commanded throttle, 0.0 to 1.0.
            current_rpm: The engine's current RPM.

        Returns:
            Engine load, 0.0 to 100.0. Dominated by throttle position,
            with a secondary contribution from how close RPM is to
            redline (representing reduced volumetric efficiency headroom
            at high RPM).
        """
        rpm_fraction = (current_rpm - const.IDLE_RPM) / (const.MAX_RPM - const.IDLE_RPM)
        rpm_fraction = max(0.0, min(1.0, rpm_fraction))

        load = throttle_percentage * 85.0 + rpm_fraction * 15.0
        return max(0.0, min(100.0, load))