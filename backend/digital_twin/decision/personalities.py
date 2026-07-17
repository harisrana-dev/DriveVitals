"""Driver personality profiles for the Decision Layer.

Personalities are sets of deterministic behavioral parameters that bias
how the Decision Layer's policies (speed/throttle/braking) interpret a
given situation. They introduce variation *between* drivers, not
randomness *within* a driver's decision-making: once resolved for a
given driver, a personality's parameters are fixed and every policy
computation from them is a pure function of its inputs.

Per the design brief, randomness is permitted only when a personality
profile is first generated during driver initialization (see
`generate_personality_profile`) -- never inside per-tick decision
logic. `DriverBehaviourEngine` only ever calls `resolve_personality_type`
and `get_personality_profile`, both of which are fully deterministic.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.entities.driver import BehaviourProfile, Driver, ExperienceLevel


class PersonalityType(str, Enum):
    """Archetype of driving personality recognized by the Decision Layer."""

    AGGRESSIVE = "AGGRESSIVE"
    NORMAL = "NORMAL"
    DEFENSIVE = "DEFENSIVE"
    ECO = "ECO"
    PROFESSIONAL = "PROFESSIONAL"
    NEW_DRIVER = "NEW_DRIVER"


@dataclass(frozen=True)
class PersonalityProfile:
    """Deterministic behavioral parameters for a driving personality.

    Attributes:
        speed_bias: Multiplier applied to the applicable speed limit
            when selecting a target speed (e.g. 1.05 drives slightly
            over the limit when conditions allow; 0.9 drives under it).
            Policies are still responsible for never exceeding the
            configured maximum speed regardless of this bias.
        acceleration_bias: Multiplier on how aggressively the driver
            wants to close the gap between current and target speed.
        braking_aggressiveness: Multiplier on how hard the driver
            brakes to reach a lower target speed.
        following_distance_seconds: Desired following distance from
            the vehicle ahead, expressed as seconds of travel time.
        risk_tolerance: 0.0 (risk-averse) to 1.0 (risk-seeking); used
            to temper how much policies scale back for adverse
            conditions.
        fuel_saving_factor: 0.0 (no regard for efficiency) to 1.0
            (maximizes efficiency); used to bias throttle/speed choices
            toward economy.
        reaction_multiplier: Baseline multiplier on reaction time,
            independent of fatigue (e.g. a NEW_DRIVER reacts more
            slowly even when fully rested). Combined multiplicatively
            with the fatigue-driven reaction multiplier from
            `FatigueModel`.
    """

    speed_bias: float
    acceleration_bias: float
    braking_aggressiveness: float
    following_distance_seconds: float
    risk_tolerance: float
    fuel_saving_factor: float
    reaction_multiplier: float

    def __post_init__(self) -> None:
        """Validate that bounded parameters stay within their defined ranges.

        Raises:
            ConfigurationError: If a [0, 1]-bounded parameter is out of
                range, or a strictly-positive parameter is not positive.
        """
        for bounded_field in ("risk_tolerance", "fuel_saving_factor"):
            value = getattr(self, bounded_field)
            if not (0.0 <= value <= 1.0):
                raise ConfigurationError(f"{bounded_field} must be between 0.0 and 1.0.")
        for positive_field in (
            "speed_bias",
            "acceleration_bias",
            "braking_aggressiveness",
            "following_distance_seconds",
            "reaction_multiplier",
        ):
            if getattr(self, positive_field) <= 0.0:
                raise ConfigurationError(f"{positive_field} must be positive.")


#: Fixed, deterministic base profile for each personality archetype.
#: These values are the single source of truth policies read from;
#: nothing in the Decision Layer mutates this mapping at runtime.
_BASE_PERSONALITY_PROFILES: Mapping[PersonalityType, PersonalityProfile] = {
    PersonalityType.AGGRESSIVE: PersonalityProfile(
        speed_bias=1.10,
        acceleration_bias=1.40,
        braking_aggressiveness=1.30,
        following_distance_seconds=1.0,
        risk_tolerance=0.85,
        fuel_saving_factor=0.15,
        reaction_multiplier=1.0,
    ),
    PersonalityType.NORMAL: PersonalityProfile(
        speed_bias=1.00,
        acceleration_bias=1.00,
        braking_aggressiveness=1.00,
        following_distance_seconds=2.0,
        risk_tolerance=0.5,
        fuel_saving_factor=0.4,
        reaction_multiplier=1.0,
    ),
    PersonalityType.DEFENSIVE: PersonalityProfile(
        speed_bias=0.92,
        acceleration_bias=0.75,
        braking_aggressiveness=0.80,
        following_distance_seconds=3.0,
        risk_tolerance=0.2,
        fuel_saving_factor=0.55,
        reaction_multiplier=1.05,
    ),
    PersonalityType.ECO: PersonalityProfile(
        speed_bias=0.90,
        acceleration_bias=0.65,
        braking_aggressiveness=0.75,
        following_distance_seconds=2.5,
        risk_tolerance=0.3,
        fuel_saving_factor=0.9,
        reaction_multiplier=1.0,
    ),
    PersonalityType.PROFESSIONAL: PersonalityProfile(
        speed_bias=0.98,
        acceleration_bias=0.90,
        braking_aggressiveness=0.95,
        following_distance_seconds=2.5,
        risk_tolerance=0.35,
        fuel_saving_factor=0.6,
        reaction_multiplier=0.95,
    ),
    PersonalityType.NEW_DRIVER: PersonalityProfile(
        speed_bias=0.88,
        acceleration_bias=0.70,
        braking_aggressiveness=0.70,
        following_distance_seconds=3.5,
        risk_tolerance=0.15,
        fuel_saving_factor=0.45,
        reaction_multiplier=1.35,
    ),
}

#: Deterministic mapping from the existing `Driver.behaviour_profile`
#: (defined in `entities/driver.py`, not modified by this sprint) to a
#: Decision Layer `PersonalityType`. Experience level can further
#: override this base mapping -- see `resolve_personality_type`.
_BEHAVIOUR_PROFILE_TO_PERSONALITY: Mapping[BehaviourProfile, PersonalityType] = {
    BehaviourProfile.AGGRESSIVE: PersonalityType.AGGRESSIVE,
    BehaviourProfile.STANDARD: PersonalityType.NORMAL,
    BehaviourProfile.CAUTIOUS: PersonalityType.DEFENSIVE,
    BehaviourProfile.ECO_FOCUSED: PersonalityType.ECO,
}


def resolve_personality_type(driver: Driver) -> PersonalityType:
    """Deterministically resolve a driver's Decision Layer personality.

    The mapping is driven by two existing, unmodified `Driver` fields:
    `behaviour_profile` gives the base archetype, and
    `experience_level` can override it -- a TRAINEE is always treated
    as NEW_DRIVER regardless of their configured behaviour profile
    (inexperience dominates), while a VETERAN with a STANDARD behaviour
    profile is treated as PROFESSIONAL (experience refines a neutral
    style into a polished one).

    Args:
        driver: The driver whose personality to resolve.

    Returns:
        The resolved PersonalityType. Always deterministic for a given
        (behaviour_profile, experience_level) pair.
    """
    if driver.experience_level == ExperienceLevel.TRAINEE:
        return PersonalityType.NEW_DRIVER

    base = _BEHAVIOUR_PROFILE_TO_PERSONALITY[driver.behaviour_profile]

    if (
        driver.experience_level == ExperienceLevel.VETERAN
        and driver.behaviour_profile == BehaviourProfile.STANDARD
    ):
        return PersonalityType.PROFESSIONAL

    return base


def get_personality_profile(personality_type: PersonalityType) -> PersonalityProfile:
    """Look up the fixed, deterministic profile for a personality type.

    Args:
        personality_type: The personality archetype to look up.

    Returns:
        The base PersonalityProfile for that archetype.
    """
    return _BASE_PERSONALITY_PROFILES[personality_type]


def generate_personality_profile(
    personality_type: PersonalityType,
    rng: random.Random,
    jitter: float = 0.05,
) -> PersonalityProfile:
    """Generate a personality profile with bounded random variation.

    Intended for use exactly once, at driver initialization/onboarding
    time (e.g. by a future Fleet onboarding workflow), to give
    individual drivers of the same archetype slightly different
    parameters. The resulting profile is then fixed for the lifetime
    of the driver and reused deterministically by the Decision Layer
    on every subsequent tick -- `DriverBehaviourEngine` never calls
    this function itself.

    Args:
        personality_type: The base archetype to vary from.
        rng: A caller-supplied `random.Random` instance. Passing a
            seeded instance makes the generated profile reproducible;
            this function never seeds or owns its own RNG (no global
            mutable state).
        jitter: Fractional amount of uniform variation to apply to
            each parameter (e.g. 0.05 varies each value by up to +/-5%).

    Returns:
        A new PersonalityProfile with each parameter independently
        varied around the archetype's base value.

    Raises:
        ConfigurationError: If jitter is negative.
    """
    if jitter < 0:
        raise ConfigurationError("jitter cannot be negative.")

    base = get_personality_profile(personality_type)

    def _vary(value: float) -> float:
        factor = 1.0 + rng.uniform(-jitter, jitter)
        return value * factor

    varied = replace(
        base,
        speed_bias=_vary(base.speed_bias),
        acceleration_bias=_vary(base.acceleration_bias),
        braking_aggressiveness=_vary(base.braking_aggressiveness),
        following_distance_seconds=_vary(base.following_distance_seconds),
        risk_tolerance=min(1.0, max(0.0, _vary(base.risk_tolerance))),
        fuel_saving_factor=min(1.0, max(0.0, _vary(base.fuel_saving_factor))),
        reaction_multiplier=_vary(base.reaction_multiplier),
    )
    return varied