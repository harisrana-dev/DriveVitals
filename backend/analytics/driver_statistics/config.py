"""
Driver statistics configuration.

Central home for every constant used by the Driver Statistics subsystem:

    * known behaviour event types and severities
    * safety score penalties
    * aggression and efficiency normalisation knobs
    * shared scoring helpers

Constants must never be scattered across driver statistics modules.
"""

# ---------------------------------------------------------------------------
# Behaviour event vocabulary
# ---------------------------------------------------------------------------

EVENT_TYPE_SPEEDING = "speeding"
EVENT_TYPE_AGGRESSIVE_THROTTLE = "aggressive_throttle"
EVENT_TYPE_HARSH_BRAKING = "harsh_braking"
EVENT_TYPE_HIGH_RPM = "high_rpm"

KNOWN_EVENT_TYPES: frozenset[str] = frozenset(
    {
        EVENT_TYPE_SPEEDING,
        EVENT_TYPE_AGGRESSIVE_THROTTLE,
        EVENT_TYPE_HARSH_BRAKING,
        EVENT_TYPE_HIGH_RPM,
    }
)

SEVERITY_NORMAL = "normal"
SEVERITY_MINOR = "minor"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE = "severe"

KNOWN_SEVERITIES: frozenset[str] = frozenset(
    {
        SEVERITY_NORMAL,
        SEVERITY_MINOR,
        SEVERITY_MODERATE,
        SEVERITY_SEVERE,
    }
)

# ---------------------------------------------------------------------------
# Safety score
# ---------------------------------------------------------------------------

# Baseline for a driver with no misbehaviour.
SAFETY_START = 100.0

# Relative weight of each behaviour type when computing weighted
# misbehaviour density.
SAFETY_WEIGHT_HARD_BRAKE = 2.0
SAFETY_WEIGHT_HARD_ACCELERATION = 1.5
SAFETY_WEIGHT_OVERSPEED = 3.0
SAFETY_WEIGHT_HIGH_RPM = 1.0

# Scales weighted misbehaviour density into a score deduction. Higher
# values make the score fall faster for the same density.
#
# The score decays exponentially with density. At this sensitivity a
# normal 3-6 km trip with 1-3 events lands in Good/Average, while a
# genuinely bad trip (density >= ~3 weighted events/km) reaches
# Poor/Critical.
SAFETY_DENSITY_SENSITIVITY = 0.35

# ---------------------------------------------------------------------------
# Aggression score
# ---------------------------------------------------------------------------

# Weighted aggression events per kilometre that yields the maximum score.
AGGRESSION_MAX_DENSITY = 1.0

AGGRESSION_WEIGHT_HARD_BRAKE = 2.0
AGGRESSION_WEIGHT_HARD_ACCELERATION = 1.5
AGGRESSION_WEIGHT_OVERSPEED = 3.0

# ---------------------------------------------------------------------------
# Efficiency score
# ---------------------------------------------------------------------------

# Behaviour events per kilometre that drive the efficiency score to zero.
EFFICIENCY_MAX_EVENTS_PER_KM = 1.0

# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def clamp_score(score: float) -> float:
    """Clamp a driver score into the valid [0, 100] range."""
    return min(100.0, max(0.0, score))


def events_per_km(count: float, distance_km: float) -> float:
    """
    Normalise an event count by distance.

    Returns the count per kilometre when distance is positive, an infinite
    density when distance is zero but events exist, and 0.0 when there is
    neither distance nor events.
    """
    if distance_km > 0.0:
        return count / distance_km
    if count > 0:
        return float("inf")
    return 0.0


__all__ = [
    "EVENT_TYPE_SPEEDING",
    "EVENT_TYPE_AGGRESSIVE_THROTTLE",
    "EVENT_TYPE_HARSH_BRAKING",
    "EVENT_TYPE_HIGH_RPM",
    "KNOWN_EVENT_TYPES",
    "SEVERITY_NORMAL",
    "SEVERITY_MINOR",
    "SEVERITY_MODERATE",
    "SEVERITY_SEVERE",
    "KNOWN_SEVERITIES",
    "SAFETY_START",
    "SAFETY_WEIGHT_HARD_BRAKE",
    "SAFETY_WEIGHT_HARD_ACCELERATION",
    "SAFETY_WEIGHT_OVERSPEED",
    "SAFETY_WEIGHT_HIGH_RPM",
    "SAFETY_DENSITY_SENSITIVITY",
    "AGGRESSION_MAX_DENSITY",
    "AGGRESSION_WEIGHT_HARD_BRAKE",
    "AGGRESSION_WEIGHT_HARD_ACCELERATION",
    "AGGRESSION_WEIGHT_OVERSPEED",
    "EFFICIENCY_MAX_EVENTS_PER_KM",
    "clamp_score",
    "events_per_km",
]
