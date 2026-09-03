"""
OBD Generator.

Generates continuous, internally-consistent OBD-like telemetry for a
single vehicle over time. This is the only place that "makes up"
sensor numbers — it never outputs analytics conclusions (e.g. it will
never emit something like `driver_is_aggressive = True`). It only
produces raw, plausible measurements; DriveVitals analytics is
responsible for interpreting them.

Behavior-profile driven differences (see fleet.models.driver.BehaviorProfile):

    AGGRESSIVE  higher acceleration variance, harder braking,
                higher RPM, higher fuel consumption, more speed variation
    ECO         smoother acceleration, lower RPM, lower fuel
                consumption, stable speed
    CAUTIOUS    gentler acceleration/braking, lower average speed
    STANDARD    normal driving variation

Internal consistency rules implemented:
  * Speed changes smoothly (bounded acceleration per tick), never jumps.
  * RPM is derived from speed (a simple gear model), so it tracks speed.
  * Fuel rate scales with RPM and engine load, so harder driving burns
    more fuel.
  * Coolant temperature warms up gradually toward an operating
    temperature and responds slightly to engine load; it never jumps.
  * Odometer / trip distance increase continuously with distance
    actually travelled this tick.
"""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from backend.fleet.models.driver import BehaviorProfile
from backend.fleet.models.route import Route
from backend.fleet.runtime.runtime_state import RuntimeState
from backend.telemetry.models.telemetry_sample import TelemetrySample
from backend.fleet.models.route import RouteType

# Tunable per-profile characteristics. These are simulation inputs
# only, not analytics labels.
_PROFILE_PARAMS = {
    BehaviorProfile.AGGRESSIVE: dict(
        max_accel_kmh_s=6.0, max_decel_kmh_s=9.0, speed_noise=6.0,
         fuel_intensity=1.35,
    ),
    BehaviorProfile.ECO: dict(
        max_accel_kmh_s=2.0, max_decel_kmh_s=2.5, speed_noise=1.0,
         fuel_intensity=0.8,
    ),
    BehaviorProfile.CAUTIOUS: dict(
        max_accel_kmh_s=2.5, max_decel_kmh_s=3.0, speed_noise=1.5,
         fuel_intensity=0.9,
    ),
    BehaviorProfile.STANDARD: dict(
        max_accel_kmh_s=3.5, max_decel_kmh_s=5.0, speed_noise=3.0,
         fuel_intensity=1.0,
    ),
}

_ROUTE_PARAMS = {
    RouteType.URBAN: dict(
        cruising_speed_kmh=45.0,
        speed_variation=12.0,
        stop_probability=0.08,
    ),

    RouteType.HIGHWAY: dict(
        cruising_speed_kmh=105.0,
        speed_variation=8.0,
        stop_probability=0.01,
    ),

    RouteType.RURAL: dict(
        cruising_speed_kmh=75.0,
        speed_variation=15.0,
        stop_probability=0.03,
    ),
}

_OPERATING_COOLANT_TEMP_C = 90.0
_AMBIENT_COOLANT_TEMP_C = 20.0

# Brake pressure is reported relative to a single fixed reference
# deceleration, NOT the driver's profile maximum. This keeps the value
# comparable across drivers: a gentle 2.5 km/h/s stop reads ~0.3 while a
# genuinely hard 8+ km/h/s stop reads ~1.0, so harsh-braking detection
# only triggers on real hard braking instead of on every routine stop.
_BRAKE_REFERENCE_DECEL_KMH_S = 8.0


@dataclass
class OBDGenerator:
    """
    Stateful-per-tick generator for one vehicle's telemetry stream.

    Call `.step(...)` once per simulation tick; it mutates the given
    RuntimeState in place and returns the TelemetrySample for that
    tick.
    """

    behavior_profile: BehaviorProfile = BehaviorProfile.STANDARD
    seed: int = 0
    _rng: random.Random = None  # type: ignore

    # Per-trip profile multipliers so the same driver profile produces
    # different but realistic behaviour across trips/runs.
    _fuel_intensity_mult: float = 1.0
    _accel_mult: float = 1.0
    _decel_mult: float = 1.0
    _speed_factor_offset: float = 0.0

    def __post_init__(self) -> None:
        if self._rng is None:
            self._rng = random.Random(self.seed)
        self._fuel_intensity_mult = self._rng.uniform(0.90, 1.10)
        self._accel_mult = self._rng.uniform(0.95, 1.05)
        self._decel_mult = self._rng.uniform(0.95, 1.05)
        self._speed_factor_offset = self._rng.uniform(-0.05, 0.05)

    def step(
        self,
        *,
        now: datetime,
        dt_seconds: float,
        runtime_state: RuntimeState,
        route: Route,
        vehicle_id: str,
        driver_id: str,
        trip_id: str,
        vehicle_odometer_km: float,
        vehicle_fuel_level_percent: float,
        tank_capacity_liters: float = 60.0,
        fuel_efficiency_factor: float = 1.0,
        acceleration_response: float = 1.0,
    ) -> Tuple[TelemetrySample, float, float]:
        """
        Advance the simulation by `dt_seconds` and produce one
        telemetry sample.

        Returns (sample, distance_travelled_km_this_tick,
        fuel_used_percent_this_tick) so callers (VehicleRunner) can
        update the persistent Vehicle's odometer and fuel level, and
        the Trip's distance travelled, without duplicating the
        physics here.
        """
        params = _PROFILE_PARAMS[self.behavior_profile]

# Apply per-trip variation to profile params.
        effective_max_accel = (
            params["max_accel_kmh_s"]
            * self._accel_mult
            * acceleration_response
        )
        effective_max_decel = (
            params["max_decel_kmh_s"]
            * self._decel_mult
            * acceleration_response
        )
        # A vehicle's fuel efficiency factor scales how much fuel its
        # engine burns for a given load. Lower factor = more efficient.
        effective_fuel_intensity = (
            params["fuel_intensity"]
            * self._fuel_intensity_mult
            * max(0.1, 2.0 - fuel_efficiency_factor)
        )

        route_params = _ROUTE_PARAMS[route.route_type]

        base_cruising_speed = route_params["cruising_speed_kmh"]

# Driver behavior influences how the driver tends to operate
# within that environment. Per-trip offset adds run-to-run variation.
        if self.behavior_profile == BehaviorProfile.AGGRESSIVE:
            behavior_speed_factor = 1.15 + self._speed_factor_offset
        elif self.behavior_profile == BehaviorProfile.ECO:
            behavior_speed_factor = 0.90 + self._speed_factor_offset
        elif self.behavior_profile == BehaviorProfile.CAUTIOUS:
            behavior_speed_factor = 0.80 + self._speed_factor_offset
        else:
            behavior_speed_factor = 1.0 + self._speed_factor_offset

        target_speed = base_cruising_speed * behavior_speed_factor

# Traffic variation: random slowdown/stop events.
        stop_probability = route_params["stop_probability"] * dt_seconds
        if self._rng.random() < stop_probability:
            target_speed *= self._rng.uniform(0.3, 0.7)

# Natural variation in the target speed.
        target_speed += self._rng.uniform(
           -route_params["speed_variation"],
            route_params["speed_variation"],
        )

        target_speed = max(0.0, target_speed)

        current_speed = runtime_state.current_speed_kmh
        speed_gap = target_speed - current_speed
        max_delta = (
            effective_max_accel if speed_gap >= 0 else effective_max_decel
        ) * dt_seconds
        speed_delta = max(-max_delta, min(max_delta, speed_gap))
        new_speed = max(0.0, current_speed + speed_delta)

        # --- Brake pressure: proportional to how hard we're
        # decelerating relative to the fixed reference deceleration.
        if speed_delta < 0:
            brake_pressure = min(
                1.0,
                abs(speed_delta)
                / (_BRAKE_REFERENCE_DECEL_KMH_S * dt_seconds + 1e-6),
            )
            brake_pressure += self._rng.uniform(0.0, 0.05)  # braking noise
            brake_pressure = min(1.0, brake_pressure)
        else:
            brake_pressure = self._rng.uniform(0.0, 0.02) if new_speed > 0 else 0.0

        # --- Throttle: proportional to how hard we're accelerating.
        if speed_delta > 0:
            throttle = min(100.0, 40.0 + 60.0 * (speed_delta / (effective_max_accel * dt_seconds + 1e-6)))
        else:
            throttle = 0.0 if new_speed == 0 else 15.0  # light throttle to hold cruise
            throttle += self._rng.uniform(-3.0, 3.0)  # throttle noise
            throttle = max(0.0, min(100.0, throttle))

        # --- RPM: simple gear-based estimate so RPM tracks speed
        # instead of being generated independently.
        rpm = self._estimate_rpm(new_speed)

        # --- Engine load: combination of throttle and RPM, used to
        # drive fuel rate and coolant temperature.
        engine_load = min(100.0, 0.6 * throttle + 0.4 * (rpm / 6000.0 * 100.0))

        # --- Fuel rate: baseline idle burn plus load-driven
        # consumption, scaled by per-trip profile fuel intensity.
        fuel_rate = (0.5 + (engine_load / 100.0) * 8.0) * effective_fuel_intensity

        # --- Coolant temperature: warms gradually toward operating
        # temperature, nudged slightly by engine load; never jumps.
        current_temp = runtime_state.current_engine_temperature_c
        warm_rate_c_per_s = 0.05 + (engine_load / 100.0) * 0.02
        temp_gap = _OPERATING_COOLANT_TEMP_C - current_temp
        temp_delta = max(-2.0, min(2.0, temp_gap * warm_rate_c_per_s * dt_seconds))
        new_temp = max(_AMBIENT_COOLANT_TEMP_C, current_temp + temp_delta)

        # --- Distance travelled this tick.
        distance_km = new_speed * (dt_seconds / 3600.0)

        # --- Fuel level: drawn down using fuel_rate over dt, expressed
        # as a percentage of the tank so it can be applied directly to
        # Vehicle.fuel_level_percent by the caller.
        fuel_used_liters = fuel_rate * (dt_seconds / 3600.0)
        fuel_used_percent = min(
            vehicle_fuel_level_percent, (fuel_used_liters / tank_capacity_liters) * 100.0
        )
        new_fuel_level_percent = max(0.0, vehicle_fuel_level_percent - fuel_used_percent)

        # Mutate runtime state for next tick.
        runtime_state.current_speed_kmh = new_speed
        runtime_state.current_rpm = rpm
        runtime_state.current_fuel_rate_lph = fuel_rate
        runtime_state.current_engine_temperature_c = new_temp
        runtime_state.current_trip_distance_km += distance_km

        sample = TelemetrySample(
            timestamp=now,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            trip_id=trip_id,
            speed_kmh=round(new_speed, 2),
            rpm=round(rpm, 0),
            throttle_position_percent=round(throttle, 1),
            brake_pressure=round(brake_pressure, 2),
            coolant_temperature_c=round(new_temp, 1),
            engine_load_percent=round(engine_load, 1),
            fuel_rate_lph=round(fuel_rate, 2),
            fuel_level_percent=round(new_fuel_level_percent, 2),
            odometer_km=round(vehicle_odometer_km + distance_km, 2),
        )

        return sample, distance_km, fuel_used_percent

    @staticmethod
    def _estimate_rpm(speed_kmh: float) -> float:
        """
        Simple gear-based RPM estimate. Not a real transmission
        model — just enough to keep RPM correlated with speed rather
        than independently random.
        """
        idle_rpm = 800.0
        if speed_kmh <= 0.5:
            return idle_rpm

        # Rough gear bands (km/h upper bound -> effective RPM-per-kmh)
        gear_bands = [
            (20, 45.0),
            (40, 30.0),
            (65, 22.0),
            (100, 16.0),
            (float("inf"), 11.0),
        ]
        for upper_bound, rpm_per_kmh in gear_bands:
            if speed_kmh <= upper_bound:
                return min(6500.0, idle_rpm + speed_kmh * rpm_per_kmh * 0.4 + speed_kmh * 8)
        return idle_rpm