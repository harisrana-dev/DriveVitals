"""ResistanceModel: forces and traction limits that oppose vehicle motion.

Computes rolling resistance and aerodynamic drag forces, plus a
combined traction (grip) factor derived from weather, road surface,
and road condition -- used by Dynamics to cap the acceleration/braking
force the vehicle can actually apply, and by WearModel to scale tyre
wear. Contains no decision-making: every method is a pure function of
its inputs.
"""

from __future__ import annotations

from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.physics import physics_constants as const


class ResistanceModel:
    """Computes resistive forces and traction limits from vehicle/environment state.

    Stateless: every method is a pure function of its arguments.
    """

    def compute_rolling_resistance_force_n(
        self,
        mass_kg: float,
        rolling_resistance_coefficient: float = const.DEFAULT_ROLLING_RESISTANCE_COEFFICIENT,
    ) -> float:
        """Compute the rolling resistance force opposing motion.

        Args:
            mass_kg: Vehicle mass, in kilograms.
            rolling_resistance_coefficient: Dimensionless rolling
                resistance coefficient for the tyre/road pairing.

        Returns:
            Rolling resistance force, in Newtons. Always non-negative;
            Dynamics is responsible for applying it opposite to the
            direction of travel.
        """
        return rolling_resistance_coefficient * mass_kg * const.GRAVITY_MPS2

    def compute_aerodynamic_drag_force_n(
        self,
        speed_kmh: float,
        drag_coefficient: float = const.DEFAULT_DRAG_COEFFICIENT,
        frontal_area_m2: float = const.DEFAULT_FRONTAL_AREA_M2,
    ) -> float:
        """Compute the aerodynamic drag force opposing motion.

        Args:
            speed_kmh: Vehicle speed, in km/h.
            drag_coefficient: Dimensionless aerodynamic drag coefficient.
            frontal_area_m2: Vehicle frontal area, in square meters.

        Returns:
            Aerodynamic drag force, in Newtons. Always non-negative;
            scales with the square of speed.
        """
        speed_mps = max(0.0, speed_kmh) * const.KMH_TO_MPS
        return (
            0.5
            * const.AIR_DENSITY_KG_M3
            * drag_coefficient
            * frontal_area_m2
            * speed_mps**2
        )

    def compute_grade_force_n(
        self,
        mass_kg: float,
        road_grade_percent: float = 0.0,
    ) -> float:
        """Compute the force from road gradient (positive = uphill).

        Road/route data is not part of the Physics Engine's current
        input signature (`Vehicle`, `VehicleActuation`,
        `EnvironmentSnapshot`, `TickContext` -- no `Route`), so this
        defaults to a flat road (0.0). The parameter exists so gradient
        support is already implemented and ready to use once route
        grade data is threaded into the pipeline in a future sprint.

        Args:
            mass_kg: Vehicle mass, in kilograms.
            road_grade_percent: Road gradient as a percentage (e.g.
                5.0 for a 5% uphill grade, -5.0 for downhill).

        Returns:
            The gradient force, in Newtons. Positive opposes forward
            motion (uphill), negative assists it (downhill).
        """
        grade_fraction = road_grade_percent / 100.0
        return mass_kg * const.GRAVITY_MPS2 * grade_fraction

    def compute_traction_factor(self, environment: EnvironmentSnapshot) -> float:
        """Compute the combined traction (grip) multiplier for current conditions.

        Args:
            environment: Current environmental conditions.

        Returns:
            A traction multiplier in (0.0, 1.0], applied by Dynamics to
            cap available acceleration/braking force. 1.0 means full,
            dry-road grip; lower values mean reduced grip.
        """
        weather_factor = const.WEATHER_GRIP_FACTORS.get(environment.weather, 1.0)
        surface_factor = const.ROAD_SURFACE_GRIP_FACTORS.get(environment.road_surface, 1.0)
        condition_factor = const.ROAD_CONDITION_GRIP_FACTORS.get(
            environment.road_condition, 1.0
        )

        combined = weather_factor * surface_factor * condition_factor

        if environment.rain_intensity_mm_per_hour >= const.HEAVY_RAIN_INTENSITY_MM_PER_HOUR:
            combined *= const.HEAVY_RAIN_GRIP_FACTOR

        return max(0.05, min(1.0, combined))