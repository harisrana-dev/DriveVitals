"""Physics constants and default vehicle physical properties.

Every numeric constant used anywhere in the Physics Engine lives here.
No submodel hardcodes a value of its own.

INTERFACE GAP (reported, not silently patched around):
    `digital_twin.entities.vehicle.VehicleSpecification` -- which this
    sprint is expressly forbidden from modifying -- carries only
    `manufacturer`, `model`, `year`, `fuel_type`, and `transmission`.
    It has no mass, drag coefficient, frontal area, fuel/energy tank
    capacity, idle RPM, or max RPM: the physical properties a Dynamics/
    Powertrain/Fuel model needs. Rather than inventing per-vehicle
    values with no data to derive them from, this module defines a
    single set of fleet-wide default physical constants
    (`DEFAULT_VEHICLE_MASS_KG`, `DEFAULT_DRAG_COEFFICIENT`, etc.) that
    the Physics Engine applies to every vehicle uniformly. This keeps
    `PhysicsEngine.update()`'s signature exactly matching the brief
    (Vehicle, VehicleActuation, EnvironmentSnapshot, TickContext -- no
    extra required parameter), at the cost of not yet differentiating
    physics between vehicle types. See the module-level "INTERFACE
    MISMATCH REPORT" in `physics_engine.py` for the full writeup and
    the recommended fix (extending `VehicleSpecification` in a future
    sprint, or introducing a keyed physics-profile lookup).
"""

from __future__ import annotations

from digital_twin.common.enums import RoadCondition, WeatherCondition
from digital_twin.entities.environment import RoadSurface
from digital_twin.entities.vehicle import FuelType

# --- Environment ------------------------------------------------------------

GRAVITY_MPS2: float = 9.81
AIR_DENSITY_KG_M3: float = 1.225

# --- Default vehicle physical properties (fleet-wide; see gap above) ------

DEFAULT_VEHICLE_MASS_KG: float = 2_500.0
DEFAULT_DRAG_COEFFICIENT: float = 0.35
DEFAULT_FRONTAL_AREA_M2: float = 3.6
DEFAULT_ROLLING_RESISTANCE_COEFFICIENT: float = 0.012
DEFAULT_TANK_CAPACITY_LITERS: float = 80.0

#: Maximum forward force the powertrain can deliver at full throttle,
#: in Newtons -- a fleet-wide approximation standing in for a real
#: torque/gearing curve.
DEFAULT_MAX_ENGINE_FORCE_N: float = 6_000.0

#: Maximum braking force at full brake, in Newtons.
DEFAULT_MAX_BRAKE_FORCE_N: float = 9_000.0

# --- Acceleration/deceleration clamps ---------------------------------------

MAX_ACCELERATION_MPS2: float = 3.5
MAX_DECELERATION_MPS2: float = 9.0

#: Additional deceleration from engine braking (compression braking)
#: when the throttle is closed, the transmission is engaged, and the
#: vehicle is still moving.
ENGINE_BRAKING_DECELERATION_MPS2: float = 0.6

# --- Powertrain --------------------------------------------------------------

IDLE_RPM: float = 800.0
MAX_RPM: float = 4_500.0
REDLINE_RPM: float = 4_800.0

#: RPM contributed per km/h of speed, per numbered gear (1-7). Higher
#: gears produce less RPM for the same road speed, matching how real
#: gearing works. Values are fleet-wide defaults (see module gap note).
GEAR_RPM_PER_KMH: dict[int, float] = {
    1: 55.0,
    2: 38.0,
    3: 27.0,
    4: 20.0,
    5: 15.0,
    6: 12.0,
    7: 10.0,
}

#: Maximum RPM change allowed per tick-second, preventing unrealistic
#: instantaneous jumps (e.g. idle to redline in one tick).
MAX_RPM_DELTA_PER_SECOND: float = 2_500.0

# --- Fuel / energy -----------------------------------------------------------

#: Fuel/energy burned at idle, in liters (or liter-equivalent for
#: electric/hybrid) per hour.
IDLE_FUEL_RATE_L_PER_HOUR: float = 0.8

#: Additional fuel/energy burned per 1.0 (100%) of engine load, per hour.
LOAD_FUEL_RATE_L_PER_HOUR: float = 14.0

#: Per-fuel-type multiplier applied to the consumption formula, modeling
#: relative efficiency differences without a real efficiency curve.
FUEL_TYPE_CONSUMPTION_FACTOR: dict[FuelType, float] = {
    FuelType.GASOLINE: 1.0,
    FuelType.DIESEL: 0.85,
    FuelType.HYBRID: 0.6,
    FuelType.ELECTRIC: 0.3,
    FuelType.CNG: 0.9,
}

# --- Thermal -----------------------------------------------------------------

DEFAULT_AMBIENT_TEMPERATURE_C: float = 20.0
ENGINE_OPERATING_TEMPERATURE_C: float = 90.0
MAX_SAFE_ENGINE_TEMPERATURE_C: float = 105.0
OVERHEAT_TEMPERATURE_C: float = 115.0

#: Time constant, in seconds, for engine temperature to approach its
#: current heat-generation-driven target (smaller = faster warm-up).
THERMAL_TIME_CONSTANT_SECONDS: float = 180.0

# --- Wear --------------------------------------------------------------------

#: Baseline tyre wear, in percentage points, per km driven at a
#: reference speed and grip level.
TYRE_WEAR_PERCENT_PER_KM: float = 0.0015

#: Reference speed, in km/h, above which tyre wear accelerates.
TYRE_WEAR_REFERENCE_SPEED_KMH: float = 90.0

#: Brake wear, in percentage points, per unit of (brake_percentage *
#: speed_kmh * delta_time_hours) -- i.e. harder braking at higher
#: speed wears pads faster.
BRAKE_WEAR_PERCENT_PER_UNIT: float = 0.02

#: Engine health degradation, in percentage points, per engine-hour at
#: the reference RPM/temperature.
ENGINE_DEGRADATION_PERCENT_PER_HOUR: float = 0.01

#: Additional engine degradation multiplier applied while the engine
#: temperature exceeds `MAX_SAFE_ENGINE_TEMPERATURE_C`.
OVERHEAT_DEGRADATION_MULTIPLIER: float = 5.0

#: Oil life consumed, in percentage points, per engine-hour at nominal
#: load. Not persisted to `VehicleState` (no such field exists yet);
#: reported via `PhysicsTickResult` only -- see the interface mismatch
#: report in `physics_engine.py`.
OIL_LIFE_PERCENT_PER_ENGINE_HOUR: float = 0.08

# --- Traction / grip ---------------------------------------------------------

#: Multiplier on available traction (0.0-1.0) per weather condition.
#: Lower values mean less grip is available for acceleration/braking.
WEATHER_GRIP_FACTORS: dict[WeatherCondition, float] = {
    WeatherCondition.CLEAR: 1.00,
    WeatherCondition.RAIN: 0.80,
    WeatherCondition.FOG: 0.90,
    WeatherCondition.SNOW: 0.55,
    WeatherCondition.STORM: 0.60,
}

#: Multiplier on available traction per road surface condition.
ROAD_SURFACE_GRIP_FACTORS: dict[RoadSurface, float] = {
    RoadSurface.DRY: 1.00,
    RoadSurface.WET: 0.80,
    RoadSurface.ICY: 0.35,
    RoadSurface.SNOWY: 0.50,
    RoadSurface.MUDDY: 0.65,
}

#: Multiplier on available traction per discrete road condition/event.
ROAD_CONDITION_GRIP_FACTORS: dict[RoadCondition, float] = {
    RoadCondition.NORMAL: 1.00,
    RoadCondition.CONGESTED: 0.95,
    RoadCondition.CONSTRUCTION: 0.85,
    RoadCondition.ACCIDENT: 0.85,
    RoadCondition.CLOSED: 1.00,
}

#: Rain intensity, in mm/hour, at or above which grip is reduced to its
#: minimum regardless of the discrete `WeatherCondition` grip factor.
HEAVY_RAIN_INTENSITY_MM_PER_HOUR: float = 7.5

#: Grip multiplier applied additionally when rain intensity is at or
#: above `HEAVY_RAIN_INTENSITY_MM_PER_HOUR`.
HEAVY_RAIN_GRIP_FACTOR: float = 0.75

# --- Numerical stability -----------------------------------------------------

#: Speed, in km/h, below which the vehicle is treated as fully stopped
#: for resistance-force purposes (avoids division/sign issues at v=0).
STOPPED_SPEED_EPSILON_KMH: float = 0.05

#: Conversion factor: km/h to m/s.
KMH_TO_MPS: float = 1.0 / 3.6

#: Conversion factor: m/s to km/h.
MPS_TO_KMH: float = 3.6