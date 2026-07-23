"""
Driver model.

Represents a real driver. May carry a configurable behavior profile
that influences how the simulator generates telemetry (e.g. an
"aggressive" profile produces sharper acceleration and braking
patterns). The profile is a simulation input, not an analytics
conclusion — DriveVitals analytics is what later decides, from
telemetry, whether a driver's actual behavior was risky or efficient.
"""

from dataclasses import dataclass
from enum import Enum


class BehaviorProfile(str, Enum):
    AGGRESSIVE = "aggressive"
    CAUTIOUS = "cautious"
    ECO = "eco"
    STANDARD = "standard"


@dataclass
class Driver:
    driver_id: str
    name: str
    behavior_profile: BehaviorProfile = BehaviorProfile.STANDARD