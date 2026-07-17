"""FuelModel: fuel/energy consumption, tank level, and remaining range.

`VehicleState` has a single `fuel_level_percent` field used uniformly
for fuel and battery charge (see the interface mismatch report in
`physics_engine.py` for the full discussion of what's *not* modeled --
notably there is no `fuel_consumed` cumulative field). This model
computes consumption for the current tick and returns it explicitly
(via `PhysicsTickResult`, not persisted elsewhere) alongside updating
`fuel_level_percent`.
"""

from __future__ import annotations

from digital_twin.entities.vehicle import FuelType
from digital_twin.physics import physics_constants as const


class FuelModel:
    """Computes fuel/energy consumption and updates tank level.

    Stateless: every method is a pure function of its arguments.
    """

    def compute_fuel_rate_l_per_hour(
        self,
        rpm: float,
        throttle_percentage: float,
        engine_load_percent: float,
        fuel_type: FuelType,
    ) -> float:
        """Compute the instantaneous fuel/energy consumption rate.

        Args:
            rpm: Current engine RPM. Reserved for future refinement
                (e.g. a real BSFC curve); the current linear model uses
                `engine_load_percent` as RPM's effect is already
                reflected there via `Powertrain.compute_engine_load_percent`.
            throttle_percentage: Commanded throttle, 0.0 to 1.0.
            engine_load_percent: Current engine load, 0.0 to 100.0.
            fuel_type: The vehicle's fuel/energy type, used to apply a
                relative efficiency multiplier.

        Returns:
            Fuel/energy consumption rate, in liters (or
            liter-equivalent) per hour. Always non-negative.
        """
        del rpm  # Reserved for a future non-linear RPM/BSFC refinement.

        load_fraction = engine_load_percent / 100.0
        base_rate = const.IDLE_FUEL_RATE_L_PER_HOUR + load_fraction * const.LOAD_FUEL_RATE_L_PER_HOUR
        # Throttle alone (before load fully ramps up) still burns a
        # little extra, avoiding a rate that depends on load only.
        throttle_contribution = throttle_percentage * 0.5

        factor = const.FUEL_TYPE_CONSUMPTION_FACTOR.get(fuel_type, 1.0)
        return max(0.0, (base_rate + throttle_contribution) * factor)

    def compute_fuel_consumed_liters(
        self, fuel_rate_l_per_hour: float, delta_time_seconds: float
    ) -> float:
        """Compute fuel/energy consumed during this tick.

        Args:
            fuel_rate_l_per_hour: Instantaneous consumption rate.
            delta_time_seconds: Simulated seconds elapsed this tick.

        Returns:
            Fuel/energy consumed this tick, in liters (or
            liter-equivalent).
        """
        return fuel_rate_l_per_hour * (delta_time_seconds / 3600.0)

    def update_fuel_level_percent(
        self,
        current_fuel_percent: float,
        fuel_consumed_liters: float,
        tank_capacity_liters: float = const.DEFAULT_TANK_CAPACITY_LITERS,
    ) -> float:
        """Update the fuel/battery level after consuming fuel this tick.

        Args:
            current_fuel_percent: Fuel level at the start of this tick.
            fuel_consumed_liters: Fuel/energy consumed this tick.
            tank_capacity_liters: Total tank/battery capacity.

        Returns:
            The new fuel level, clamped to `[0.0, 100.0]`.
        """
        if tank_capacity_liters <= 0.0:
            return current_fuel_percent
        percent_consumed = (fuel_consumed_liters / tank_capacity_liters) * 100.0
        return max(0.0, min(100.0, current_fuel_percent - percent_consumed))

    def estimate_remaining_range_km(
        self,
        fuel_level_percent: float,
        tank_capacity_liters: float,
        average_consumption_l_per_100km: float,
    ) -> float:
        """Estimate remaining driving range from current fuel level.

        Args:
            fuel_level_percent: Current fuel level, 0.0 to 100.0.
            tank_capacity_liters: Total tank/battery capacity.
            average_consumption_l_per_100km: Recent average consumption
                rate, in liters per 100 km. If 0.0 (e.g. no driving
                history yet), range cannot be estimated.

        Returns:
            Estimated remaining range, in kilometers. 0.0 if
            `average_consumption_l_per_100km` is not positive.
        """
        if average_consumption_l_per_100km <= 0.0:
            return 0.0
        remaining_liters = (fuel_level_percent / 100.0) * tank_capacity_liters
        return (remaining_liters / average_consumption_l_per_100km) * 100.0