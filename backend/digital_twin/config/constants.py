"""System-wide constants for the DriveVitals Digital Twin.

This module is the single source of truth for default numeric values
used across the configuration layer. `defaults.py` and
`simulation_config.py` both read from here so a value never needs to
be changed in more than one place.

These are constants only -- no logic, no classes, no I/O.
"""

from __future__ import annotations

# --- Clock ---------------------------------------------------------------

#: Real-world seconds between ticks when the runtime paces itself in
#: real time (see DigitalTwinRuntime.run_for(real_time_delay=True)).
DEFAULT_TICK_INTERVAL_SECONDS: float = 1.0

#: Simulated seconds that elapse per tick at 1x clock speed.
DEFAULT_SIMULATED_SECONDS_PER_TICK: float = 1.0

#: Default clock speed multiplier: 1 real second of stepping ==
#: 1 simulated minute.
DEFAULT_CLOCK_SPEED: float = 1.0

#: Clock speed multipliers the platform is expected to support in the
#: UI/API (informational; SimulationClock itself accepts any positive
#: float, this list is for validation layers built on top of it).
SUPPORTED_CLOCK_MULTIPLIERS: tuple[float, ...] = (1.0, 10.0, 30.0, 60.0, 120.0, 300.0)

# --- Fleet -----------------------------------------------------------------

#: Maximum number of vehicles a single fleet may register.
MAX_FLEET_SIZE: int = 10_000

#: Maximum number of drivers a single fleet may register.
MAX_DRIVER_COUNT: int = 10_000

# --- Driver ------------------------------------------------------------

#: Maximum continuous working hours before a mandatory break is forced.
DEFAULT_MAX_WORKING_HOURS_PER_SHIFT: float = 10.0

#: Minimum mandatory break duration, in minutes.
DEFAULT_MANDATORY_BREAK_MINUTES: float = 30.0

#: Continuous working hours after which a driver is flagged FATIGUED.
DEFAULT_FATIGUE_THRESHOLD_HOURS: float = 8.0

# --- Vehicle -------------------------------------------------------------

#: Default distance, in km, until a newly onboarded vehicle's first
#: scheduled service.
DEFAULT_SERVICE_INTERVAL_KM: float = 10_000.0

# --- Trip ------------------------------------------------------------------

#: Default maximum number of trips a fleet may hold active at once.
DEFAULT_MAX_ACTIVE_TRIPS: int = 5_000

# --- Maintenance -----------------------------------------------------------

#: Distance, in km, remaining before a scheduled service at which
#: status becomes DUE_SOON.
DEFAULT_DUE_SOON_MILEAGE_THRESHOLD_KM: float = 500.0

#: Days between mandatory vehicle inspections.
DEFAULT_INSPECTION_INTERVAL_DAYS: int = 180

# --- Environment -------------------------------------------------------

#: Weather condition the simulation starts in (string form of
#: WeatherCondition to avoid a config -> enums import dependency here).
DEFAULT_WEATHER: str = "CLEAR"

#: Seed for environment-related randomness (variation only, never
#: behavior-driving, per Digital Twin principle #3).
DEFAULT_ENVIRONMENT_RANDOM_SEED: int = 42

# --- Telemetry ---------------------------------------------------------

#: Maximum telemetry sampling frequency, in Hz, a vehicle may stream at.
MAX_TELEMETRY_FREQUENCY_HZ: float = 10.0

#: Default telemetry sampling frequency, in Hz.
DEFAULT_TELEMETRY_FREQUENCY_HZ: float = 1.0

#: Default number of telemetry samples retained in memory per vehicle
#: before older samples are dropped (future Telemetry module concern;
#: value lives here so it is configured, not hardcoded, when needed).
DEFAULT_TELEMETRY_BUFFER_SIZE: int = 3_600

# --- Analytics -----------------------------------------------------

#: Default rolling window, in simulated minutes, analytics aggregates
#: use when no explicit window is provided.
DEFAULT_ANALYTICS_WINDOW_MINUTES: float = 15.0

#: Default refresh interval, in ticks, between analytics recomputation.
DEFAULT_ANALYTICS_REFRESH_TICKS: int = 60