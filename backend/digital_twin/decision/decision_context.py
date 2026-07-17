"""DecisionContext: the single input object for the Decision Layer.

Aggregates every reference and scalar the `DriverBehaviourEngine` needs
so it can be called with one object instead of a long parameter list.
Entirely read-only from the Decision Layer's perspective: nothing here
is mutated by decision logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.entities.cargo import Cargo
from digital_twin.entities.driver import Driver
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.route import Route
from digital_twin.entities.trip import Trip
from digital_twin.entities.vehicle import Vehicle
from digital_twin.runtime.tick_context import TickContext


@dataclass(frozen=True)
class DecisionContext:
    """Immutable snapshot of everything needed to decide driver intent.

    Attributes:
        driver: The driver making this decision.
        vehicle: The vehicle currently assigned to the driver.
        trip: The trip currently in progress, if any (None if the
            driver/vehicle pairing is not currently on a trip).
        route: The route associated with the current trip, if any.
        cargo: The cargo associated with the current trip, if any.
        environment: Current environmental conditions.
        tick_context: The simulation's immutable per-tick context.
        current_speed_kmh: The vehicle's current speed, read from
            `vehicle.state.current_speed_kmh` at the time this context
            was built (duplicated here so policies don't need to know
            `Vehicle`'s internal shape).
        current_fatigue_level: The driver's current fatigue level, on a
            0.0-1.0 scale, as already tracked on `driver.fatigue_level`.
        current_speed_limit_kmh: The speed limit applicable at the
            vehicle's current position. Not read directly from `route`
            because a route's `speed_limits_kmh` is a per-segment
            profile; whoever builds this context is responsible for
            resolving "current position" to "current segment" and
            supplying the single applicable value here.
        continuous_driving_hours: Hours driven continuously since the
            driver's last break, for use by `FatigueModel`.
        break_duration_minutes: Duration of the driver's most recent
            break, in minutes, for use by `FatigueModel`.
        shift_duration_hours: Elapsed duration of the driver's current
            shift, in hours, for use by `FatigueModel`.
    """

    driver: Driver
    vehicle: Vehicle
    trip: Trip | None
    route: Route | None
    cargo: Cargo | None
    environment: EnvironmentSnapshot
    tick_context: TickContext
    current_speed_kmh: float
    current_fatigue_level: float
    current_speed_limit_kmh: float
    continuous_driving_hours: float
    break_duration_minutes: float
    shift_duration_hours: float

    def __post_init__(self) -> None:
        """Validate scalar inputs.

        Raises:
            ConfigurationError: If any speed/duration is negative, or
                current_fatigue_level is outside [0.0, 1.0].
        """
        if self.current_speed_kmh < 0:
            raise ConfigurationError("current_speed_kmh cannot be negative.")
        if self.current_speed_limit_kmh < 0:
            raise ConfigurationError("current_speed_limit_kmh cannot be negative.")
        if not (0.0 <= self.current_fatigue_level <= 1.0):
            raise ConfigurationError("current_fatigue_level must be between 0.0 and 1.0.")
        for duration_field in (
            "continuous_driving_hours",
            "break_duration_minutes",
            "shift_duration_hours",
        ):
            if getattr(self, duration_field) < 0:
                raise ConfigurationError(f"{duration_field} cannot be negative.")

    @property
    def time_of_day_hour(self) -> float:
        """float: Current simulated time of day, as fractional hours [0, 24)."""
        sim_time = self.tick_context.simulation_time
        return sim_time.hour + sim_time.minute / 60.0 + sim_time.second / 3600.0