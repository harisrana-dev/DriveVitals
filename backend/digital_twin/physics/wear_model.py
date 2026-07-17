"""WearModel: tyre wear, brake pad wear, engine degradation, oil life.

`VehicleState` exposes `tyre_wear_percent` and `brake_wear_percent`
(0.0 = new, 100.0 = fully worn) and `engine_health_percent` (100.0 =
perfect, 0.0 = failed) -- this model updates exactly those fields.
There is no `oil_life` field on `VehicleState` (see the interface
mismatch report in `physics_engine.py`); oil life is still computed
here and returned via `PhysicsTickResult` for future use, but is not
persisted anywhere.
"""

from __future__ import annotations

from digital_twin.physics import physics_constants as const


class WearModel:
    """Computes incremental wear/degradation for the current tick.

    Stateless: every method returns the *new* cumulative value given
    the *previous* one plus this tick's inputs; it holds no state of
    its own.
    """

    def update_tyre_wear_percent(
        self,
        current_tyre_wear_percent: float,
        distance_travelled_km: float,
        average_speed_kmh: float,
        traction_factor: float,
    ) -> float:
        """Update cumulative tyre wear for this tick.

        Args:
            current_tyre_wear_percent: Tyre wear at the start of this
                tick, 0.0 (new) to 100.0 (fully worn).
            distance_travelled_km: Distance travelled this tick.
            average_speed_kmh: Average speed over this tick; wear
                accelerates above the reference speed (higher speed
                increases tyre wear, per the design brief).
            traction_factor: Current traction multiplier from
                `ResistanceModel.compute_traction_factor`; lower grip
                (e.g. wet/icy roads) increases wear per km.

        Returns:
            The new cumulative tyre wear percentage, clamped to
            `[0.0, 100.0]`.
        """
        speed_multiplier = max(
            1.0, average_speed_kmh / const.TYRE_WEAR_REFERENCE_SPEED_KMH
        )
        # Reduced traction means more slip, which increases wear --
        # hence dividing by traction_factor rather than multiplying.
        grip_multiplier = 1.0 / max(0.05, traction_factor)

        wear_increment = (
            distance_travelled_km
            * const.TYRE_WEAR_PERCENT_PER_KM
            * speed_multiplier
            * grip_multiplier
        )
        return max(0.0, min(100.0, current_tyre_wear_percent + wear_increment))

    def update_brake_wear_percent(
        self,
        current_brake_wear_percent: float,
        brake_percentage: float,
        current_speed_kmh: float,
        delta_time_seconds: float,
    ) -> float:
        """Update cumulative brake pad wear for this tick.

        Args:
            current_brake_wear_percent: Brake wear at the start of
                this tick, 0.0 (new) to 100.0 (fully worn).
            brake_percentage: Commanded brake this tick, 0.0 to 1.0.
            current_speed_kmh: Vehicle speed while braking; braking
                harder at higher speed wears pads faster, per the
                design brief.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            The new cumulative brake wear percentage, clamped to
            `[0.0, 100.0]`.
        """
        if brake_percentage <= 0.0:
            return current_brake_wear_percent

        delta_time_hours = delta_time_seconds / 3600.0
        wear_increment = (
            brake_percentage
            * current_speed_kmh
            * delta_time_hours
            * const.BRAKE_WEAR_PERCENT_PER_UNIT
        )
        return max(0.0, min(100.0, current_brake_wear_percent + wear_increment))

    def update_engine_health_percent(
        self,
        current_engine_health_percent: float,
        engine_temperature_c: float,
        delta_time_seconds: float,
    ) -> float:
        """Update cumulative engine health/degradation for this tick.

        Args:
            current_engine_health_percent: Engine health at the start
                of this tick, 100.0 (perfect) down to 0.0 (failed).
            engine_temperature_c: The engine's current temperature;
                degradation accelerates while overheating.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            The new engine health percentage, clamped to
            `[0.0, 100.0]`.
        """
        delta_time_hours = delta_time_seconds / 3600.0
        degradation_rate = const.ENGINE_DEGRADATION_PERCENT_PER_HOUR

        if engine_temperature_c >= const.MAX_SAFE_ENGINE_TEMPERATURE_C:
            degradation_rate *= const.OVERHEAT_DEGRADATION_MULTIPLIER

        degradation = degradation_rate * delta_time_hours
        return max(0.0, min(100.0, current_engine_health_percent - degradation))

    def compute_oil_life_percent(
        self,
        previous_oil_life_percent: float,
        delta_time_seconds: float,
        engine_load_percent: float,
    ) -> float:
        """Compute updated oil life for this tick.

        Not persisted to `VehicleState` -- no such field exists yet
        (see the interface mismatch report in `physics_engine.py`).
        Returned via `PhysicsTickResult` so the value is available to
        callers now and ready to persist once a future sprint adds an
        `oil_life_percent` field to `VehicleState`.

        Args:
            previous_oil_life_percent: Oil life carried over from the
                previous tick's `PhysicsTickResult` (the caller is
                responsible for threading this through, since it has
                nowhere to live on `VehicleState` yet).
            delta_time_seconds: Simulated seconds elapsed this tick.
            engine_load_percent: Current engine load; higher load
                consumes oil life faster.

        Returns:
            The new oil life percentage, clamped to `[0.0, 100.0]`.
        """
        delta_time_hours = delta_time_seconds / 3600.0
        load_multiplier = 0.5 + (engine_load_percent / 100.0)
        consumption = const.OIL_LIFE_PERCENT_PER_ENGINE_HOUR * delta_time_hours * load_multiplier
        return max(0.0, min(100.0, previous_oil_life_percent - consumption))