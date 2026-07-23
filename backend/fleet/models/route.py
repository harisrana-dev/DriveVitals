"""
Route model.

Represents a predefined operational journey. Provides just enough
context (distance, road type, speed limit) for telemetry generation.
No GPS, mapping, or traffic simulation is implemented.
"""

from dataclasses import dataclass
from enum import Enum


class RouteType(str, Enum):
    URBAN = "urban"
    HIGHWAY = "highway"
    RURAL = "rural"


@dataclass
class Route:
    route_id: str
    origin: str
    destination: str
    distance_km: float
    route_type: RouteType