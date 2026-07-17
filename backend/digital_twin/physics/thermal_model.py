"""ThermalModel: engine temperature warm-up, cool-down, overheat detection.

`VehicleState` has a single `engine_temperature_celsius` field (see the
interface mismatch report in `physics_engine.py`: there is no separate
`coolant_temperature`); this model treats that field as the unified
engine/coolant temperature. Temperature always moves smoothly toward a
heat-generation-driven target -- never jumps.
"""

from __future__ import annotations

import math

from digital_twin.physics import physics_constants as const


class ThermalModel:
    """Computes smooth engine temperature evolution toward a heat-driven target.

    Stateless: every method is a pure function of its arguments.
    """

    def compute_target_temperature_c(
        self,
        engine_load_percent: float,
        rpm: float,
        ambient_temperature_c: float,
    ) -> float:
        """Compute the temperature the engine is heating/cooling toward.

        Args:
            engine_load_percent: Current engine load, 0.0 to 100.0.
            rpm: Current engine RPM.
            ambient_temperature_c: Current ambient air temperature.

        Returns:
            Target temperature, in Celsius. At idle/no load the target
            approaches ambient plus a small baseline; at full load it
            approaches `ENGINE_OPERATING_TEMPERATURE_C` or slightly
            above, allowing overheat to be reachable under sustained
            high load.
        """
        load_fraction = max(0.0, min(1.0, engine_load_percent / 100.0))
        rpm_fraction = max(
            0.0,
            min(1.0, (rpm - const.IDLE_RPM) / (const.MAX_RPM - const.IDLE_RPM)),
        )
        heat_factor = 0.7 * load_fraction + 0.3 * rpm_fraction

        # At heat_factor == 0, target is just above ambient (idle
        # engine still generates some heat). At heat_factor == 1,
        # target is operating temperature plus headroom that can drift
        # into overheat territory under sustained full load.
        min_target = ambient_temperature_c + 10.0
        max_target = const.ENGINE_OPERATING_TEMPERATURE_C + 20.0
        return min_target + heat_factor * (max_target - min_target)

    def update_temperature_c(
        self,
        current_temperature_c: float,
        target_temperature_c: float,
        delta_time_seconds: float,
    ) -> float:
        """Move engine temperature smoothly toward its target.

        Uses exponential (first-order lag) approach so temperature
        never jumps: warm-up from cold and cool-down after load drops
        both follow the same smooth curve, governed by
        `THERMAL_TIME_CONSTANT_SECONDS`.

        Args:
            current_temperature_c: Temperature at the start of this
                tick.
            target_temperature_c: Temperature the engine is heating or
                cooling toward this tick, from
                `compute_target_temperature_c`.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            The new engine temperature, in Celsius.
        """
        # 1 - exp(-dt/tau) is the fraction of the remaining gap closed
        # this tick; always in (0, 1), so temperature approaches but
        # never overshoots or jumps past its target in one tick.
        fraction = 1.0 - math.exp(-delta_time_seconds / const.THERMAL_TIME_CONSTANT_SECONDS)
        return current_temperature_c + (target_temperature_c - current_temperature_c) * fraction

    def is_overheating(self, current_temperature_c: float) -> bool:
        """Determine whether the engine is currently overheating.

        Args:
            current_temperature_c: The engine's current temperature.

        Returns:
            True if temperature is at or above `OVERHEAT_TEMPERATURE_C`.
        """
        return current_temperature_c >= const.OVERHEAT_TEMPERATURE_C