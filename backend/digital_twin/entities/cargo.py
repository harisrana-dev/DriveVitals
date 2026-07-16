"""Cargo entity: domain data describing goods being transported on a trip.

Pure data model -- no loading/unloading simulation, no weight/volume
validation against vehicle capacity (that belongs to a future Physics
or Dispatch-policy sprint).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from digital_twin.common.exceptions import ConfigurationError


class CargoType(str, Enum):
    """Category of goods being transported."""

    GENERAL = "GENERAL"
    PARCEL = "PARCEL"
    PERISHABLE = "PERISHABLE"
    ELECTRONICS = "ELECTRONICS"
    CHEMICALS = "CHEMICALS"
    BULK = "BULK"
    LIVESTOCK = "LIVESTOCK"


class CargoPriority(str, Enum):
    """Delivery priority tier for a cargo load."""

    LOW = "LOW"
    STANDARD = "STANDARD"
    HIGH = "HIGH"
    URGENT = "URGENT"


@dataclass
class Cargo:
    """A single cargo load associated with a trip.

    Attributes:
        cargo_id: Unique identifier for this cargo load.
        cargo_type: Category of goods being carried.
        weight_kg: Total weight of the cargo, in kilograms.
        volume_m3: Total volume of the cargo, in cubic meters.
        priority: Delivery priority tier.
        is_fragile: Whether the cargo requires careful handling.
        is_hazardous: Whether the cargo is classified as hazardous
            material.
        loading_time_minutes: Time required to load the cargo.
        unloading_time_minutes: Time required to unload the cargo.
    """

    cargo_id: str
    cargo_type: CargoType
    weight_kg: float
    volume_m3: float
    priority: CargoPriority = CargoPriority.STANDARD
    is_fragile: bool = False
    is_hazardous: bool = False
    loading_time_minutes: float = 15.0
    unloading_time_minutes: float = 15.0

    def __post_init__(self) -> None:
        """Validate physical quantities are non-negative.

        Raises:
            ConfigurationError: If weight, volume, or timing values are
                negative.
        """
        if self.weight_kg < 0:
            raise ConfigurationError("Cargo weight_kg cannot be negative.")
        if self.volume_m3 < 0:
            raise ConfigurationError("Cargo volume_m3 cannot be negative.")
        if self.loading_time_minutes < 0 or self.unloading_time_minutes < 0:
            raise ConfigurationError("Cargo loading/unloading time cannot be negative.")