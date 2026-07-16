"""Route entity: domain data describing a planned path between two locations.

Pure data model -- no distance calculation, no ETA computation, no
pathfinding. Those belong to a future Physics/Navigation sprint; this
module only holds the data such a sprint would consume and produce.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from digital_twin.common.enums import WeatherCondition
from digital_twin.common.exceptions import ConfigurationError


class RoadType(str, Enum):
    """Category of road surface a route segment traverses."""

    HIGHWAY = "HIGHWAY"
    URBAN = "URBAN"
    RURAL = "RURAL"
    RESIDENTIAL = "RESIDENTIAL"
    UNPAVED = "UNPAVED"


class TrafficDensity(str, Enum):
    """Traffic density level for a route segment or point in time."""

    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


@dataclass
class Route:
    """A planned path between an origin and a destination.

    Profile fields (`road_types`, `speed_limits_kmh`,
    `elevation_profile_m`, `traffic_profile`, `weather_profile`) are
    parallel sequences describing the route broken into segments;
    index `i` across all profile lists describes the same segment.

    Attributes:
        route_id: Unique identifier for this route.
        origin: Free-form label/address for the starting location.
        destination: Free-form label/address for the ending location.
        distance_km: Total planned distance, in kilometers.
        estimated_duration_minutes: Total planned duration, in minutes.
        road_types: Road type for each segment along the route.
        speed_limits_kmh: Posted speed limit for each segment.
        elevation_profile_m: Elevation, in meters, at each segment.
        traffic_profile: Expected traffic density for each segment.
        weather_profile: Expected weather condition for each segment.
    """

    route_id: str
    origin: str
    destination: str
    distance_km: float
    estimated_duration_minutes: float
    road_types: list[RoadType] = field(default_factory=list)
    speed_limits_kmh: list[float] = field(default_factory=list)
    elevation_profile_m: list[float] = field(default_factory=list)
    traffic_profile: list[TrafficDensity] = field(default_factory=list)
    weather_profile: list[WeatherCondition] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate physical quantities are non-negative.

        Raises:
            ConfigurationError: If distance or duration is negative.
        """
        if self.distance_km < 0:
            raise ConfigurationError("Route distance_km cannot be negative.")
        if self.estimated_duration_minutes < 0:
            raise ConfigurationError(
                "Route estimated_duration_minutes cannot be negative."
            )