"""Environment entity: domain snapshot of world conditions.

Pure data model. This is distinct from
`digital_twin.managers.environment_manager.EnvironmentManager`, which
is the Sprint 1 runtime component that owns and mutates environment
state over time; `EnvironmentSnapshot` here is the immutable data shape
future sprints (Physics, Analytics) will read and write, decoupled from
any particular manager implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from digital_twin.common.enums import RoadCondition, WeatherCondition
from digital_twin.common.exceptions import ConfigurationError
from digital_twin.entities.route import TrafficDensity


class RoadSurface(str, Enum):
    """Physical surface condition of the road, distinct from traffic/events.

    `RoadCondition` (in `common.enums`) captures discrete road *events*
    (construction, accidents, closures); `RoadSurface` captures the
    physical surface state that affects traction.
    """

    DRY = "DRY"
    WET = "WET"
    ICY = "ICY"
    SNOWY = "SNOWY"
    MUDDY = "MUDDY"


@dataclass(frozen=True)
class Wind:
    """Wind conditions at a point in simulated time.

    Attributes:
        speed_kmh: Wind speed, in kilometers per hour.
        direction_degrees: Wind direction in compass degrees (0-359,
            where 0 is North).
    """

    speed_kmh: float = 0.0
    direction_degrees: float = 0.0

    def __post_init__(self) -> None:
        """Validate physical quantities.

        Raises:
            ConfigurationError: If speed is negative or direction is
                outside [0, 360).
        """
        if self.speed_kmh < 0:
            raise ConfigurationError("Wind speed_kmh cannot be negative.")
        if not (0.0 <= self.direction_degrees < 360.0):
            raise ConfigurationError("Wind direction_degrees must be in [0, 360).")


@dataclass(frozen=True)
class EnvironmentSnapshot:
    """Immutable snapshot of world conditions at a point in simulated time.

    Attributes:
        current_time: Simulated time this snapshot represents.
        weather: Prevailing weather condition.
        traffic_density: Prevailing traffic density.
        road_surface: Physical surface condition of the road.
        road_condition: Discrete road event/condition (construction,
            accident, closure, etc.).
        visibility_meters: Visibility distance, in meters.
        temperature_celsius: Ambient temperature, in Celsius.
        wind: Wind conditions.
        rain_intensity_mm_per_hour: Rainfall intensity, in mm/hour;
            0.0 if not raining.
        simulation_time_multiplier: Clock speed multiplier in effect
            when this snapshot was taken (simulated seconds per real
            second), mirroring `SimulationClock.clock_speed`.
    """

    current_time: datetime
    weather: WeatherCondition = WeatherCondition.CLEAR
    traffic_density: TrafficDensity = TrafficDensity.LOW
    road_surface: RoadSurface = RoadSurface.DRY
    road_condition: RoadCondition = RoadCondition.NORMAL
    visibility_meters: float = 10_000.0
    temperature_celsius: float = 20.0
    wind: Wind = Wind()
    rain_intensity_mm_per_hour: float = 0.0
    simulation_time_multiplier: float = 1.0

    def __post_init__(self) -> None:
        """Validate physical quantities.

        Raises:
            ConfigurationError: If visibility, rain intensity, or the
                simulation time multiplier is negative/non-positive.
        """
        if self.visibility_meters < 0:
            raise ConfigurationError("visibility_meters cannot be negative.")
        if self.rain_intensity_mm_per_hour < 0:
            raise ConfigurationError("rain_intensity_mm_per_hour cannot be negative.")
        if self.simulation_time_multiplier <= 0:
            raise ConfigurationError("simulation_time_multiplier must be positive.")