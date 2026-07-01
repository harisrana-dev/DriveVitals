#!/usr/bin/env python3
"""
DriveVitals - OBD-II Vehicle Telemetry Simulator (v2)
======================================================

Simulates a gasoline city car driving through realistic phases:

    IDLE -> CITY_START -> NORMAL_CITY (with TRAFFIC_STOP / AGGRESSIVE events)

This is an enhancement pass over the original simulator. The architecture,
public API (Telemetry, update(), stream(), run()) and phase model are
preserved; the internal fidelity has been substantially improved:

    1. Configurable driver profiles (Calm / Normal / Aggressive / Eco)
    2. Discrete automatic-transmission gear shifts with RPM flare & drop
    3. Torque/power based fuel model with acceleration enrichment and DFCO
    4. Additional standard OBD-II PIDs (MAF, battery voltage, IAT, STFT/LTFT,
       timing advance, absolute throttle, barometric pressure, MAP,
       fuel level, runtime & distance since start)
    5. Optional vehicle health states affecting idle stability, fuel economy,
       RPM smoothness, coolant behaviour, load, and sensor noise
    6. Small, smooth sensor-noise applied at the reporting layer only
    7. A lead-vehicle / traffic-light car-following model replacing pure
       random traffic stops (gradual slow-down, stop, resume after clear)
    8. A coolant model with cold start, warm-up, load-dependent operating
       temperature (88-100 degC healthy), and gentle cooling at long idle

Usage (standalone CLI):
    python drivevitals_simulator.py --hz 1 --profile aggressive --health worn

Usage (embedded, e.g. in FastAPI):
    sim = OBDVehicleSimulator(update_hz=5, driver_profile="eco")
    for telemetry in sim.stream():
        await websocket.send_json(telemetry.to_dict())
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Iterator, Optional


# --------------------------------------------------------------------------- #
# Enums / Data model
# --------------------------------------------------------------------------- #

class DrivePhase(str, Enum):
    IDLE = "idle"
    CITY_START = "city_start"
    NORMAL_CITY = "normal_city"
    TRAFFIC_STOP = "traffic_stop"
    AGGRESSIVE = "aggressive"


class DriverProfile(str, Enum):
    CALM = "calm"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    ECO = "eco"


class HealthState(str, Enum):
    HEALTHY = "healthy"
    SLIGHTLY_WORN = "slightly_worn"
    POORLY_MAINTAINED = "poorly_maintained"
    FAULTY = "faulty"


@dataclass(frozen=True)
class DriverProfileParams:
    accel_scale: float          # multiplier on max acceleration
    decel_scale: float          # multiplier on max (braking) deceleration
    kp_scale: float             # aggressiveness of the speed-error controller
    reaction_rate: float        # throttle actuator lag rate (higher = quicker reaction)
    throttle_noise_scale: float # driver-imprecision noise amplitude
    cruise_speed_range: tuple   # (min, max) km/h the driver is comfortable holding
    aggressive_event_scale: float  # multiplier on probability of harsh events
    throttle_gentleness: float  # <1 softens pedal application (eco hyper-miling)


DRIVER_PROFILE_PARAMS: dict[DriverProfile, DriverProfileParams] = {
    DriverProfile.CALM: DriverProfileParams(
        accel_scale=0.75, decel_scale=0.80, kp_scale=0.80, reaction_rate=3.0,
        throttle_noise_scale=0.6, cruise_speed_range=(15.0, 40.0),
        aggressive_event_scale=0.2, throttle_gentleness=0.95,
    ),
    DriverProfile.NORMAL: DriverProfileParams(
        accel_scale=1.0, decel_scale=1.0, kp_scale=1.0, reaction_rate=4.0,
        throttle_noise_scale=1.0, cruise_speed_range=(20.0, 60.0),
        aggressive_event_scale=1.0, throttle_gentleness=1.0,
    ),
    DriverProfile.AGGRESSIVE: DriverProfileParams(
        accel_scale=1.45, decel_scale=1.35, kp_scale=1.4, reaction_rate=6.0,
        throttle_noise_scale=1.35, cruise_speed_range=(30.0, 72.0),
        aggressive_event_scale=3.5, throttle_gentleness=1.1,
    ),
    DriverProfile.ECO: DriverProfileParams(
        accel_scale=0.65, decel_scale=0.85, kp_scale=0.75, reaction_rate=3.0,
        throttle_noise_scale=0.5, cruise_speed_range=(15.0, 45.0),
        aggressive_event_scale=0.05, throttle_gentleness=0.85,
    ),
}


@dataclass(frozen=True)
class HealthParams:
    idle_instability_scale: float  # amplifies idle RPM/throttle instability
    fuel_penalty_scale: float      # multiplies fuel consumption
    rpm_smoothness_scale: float    # >1 = rougher, less smooth RPM response
    coolant_target_offset: float   # shifts operating temperature target up
    coolant_ceiling_extra: float   # raises the maximum plausible coolant temp
    engine_load_offset: float      # extra parasitic load (friction/wear)
    sensor_noise_scale: float      # amplifies reported-sensor jitter
    voltage_offset: float          # weak battery/alternator droop


HEALTH_PARAMS: dict[HealthState, HealthParams] = {
    HealthState.HEALTHY: HealthParams(1.0, 1.00, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
    HealthState.SLIGHTLY_WORN: HealthParams(1.3, 1.08, 1.25, 1.5, 3.0, 3.0, 1.3, 0.15),
    HealthState.POORLY_MAINTAINED: HealthParams(1.9, 1.18, 1.6, 3.5, 6.0, 6.0, 1.8, 0.35),
    HealthState.FAULTY: HealthParams(3.0, 1.32, 2.3, 6.0, 10.0, 10.0, 2.6, 0.70),
}


@dataclass
class Telemetry:
    """A single OBD-II style telemetry snapshot."""
    # --- original core signals (unchanged names/positions) ---
    timestamp: str
    phase: str
    rpm: int
    speed_kmh: float
    throttle_position: float
    engine_load: float
    coolant_temperature: float
    fuel_rate_lph: float
    gear: int
    # --- new signals (additive) ---
    shifting: bool
    mass_air_flow_gps: float
    battery_voltage: float
    intake_air_temperature: float
    short_term_fuel_trim: float
    long_term_fuel_trim: float
    timing_advance: float
    absolute_throttle_position: float
    barometric_pressure: float
    intake_manifold_pressure: float
    fuel_level_percent: float
    runtime_since_start_s: float
    distance_since_start_km: float
    driver_profile: str
    health_state: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# --------------------------------------------------------------------------- #
# Smooth semi-random signal generator (Ornstein-Uhlenbeck process)
# --------------------------------------------------------------------------- #

class OUNoise:
    """
    Mean-reverting smooth random walk. Used instead of raw random.random()
    so signals wander realistically rather than jittering frame-to-frame.
    """

    def __init__(self, mu: float = 0.0, theta: float = 0.15, sigma: float = 1.0):
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.state = mu

    def sample(self, dt: float) -> float:
        self.state += self.theta * (self.mu - self.state) * dt
        self.state += self.sigma * math.sqrt(max(dt, 1e-6)) * random.gauss(0, 1)
        return self.state


# --------------------------------------------------------------------------- #
# Core simulator
# --------------------------------------------------------------------------- #

class OBDVehicleSimulator:
    """
    Stateful simulator of a city car's OBD-II telemetry.

    Call update() repeatedly (or iterate stream()) to advance the simulation
    by one time step and receive a Telemetry snapshot.
    """

    # Physical / tuning constants
    COOLANT_MAX = 112.0
    IDLE_DURATION_RANGE = (18.0, 30.0)          # seconds warming up at idle
    CITY_START_DURATION_RANGE = (18.0, 28.0)    # seconds ramping 0 -> city speed
    AGGRESSIVE_TOP_SPEED = 85.0
    LEAD_CRUISE_RANGE = (20.0, 55.0)            # traffic flow speed, independent of driver

    # Gear table: (upper_speed_bound_kmh, gear, rpm_per_kmh_in_gear)
    GEAR_TABLE = [
        (15.0, 1, 128.0),
        (30.0, 2, 82.0),
        (48.0, 3, 58.0),
        (68.0, 4, 42.0),
        (999.0, 5, 32.0),
    ]
    GEAR_RATIO_BY_NUMBER = {gear: ratio for _, gear, ratio in GEAR_TABLE}

    def __init__(
        self,
        update_hz: float = 1.0,
        seed: Optional[int] = None,
        driver_profile: "DriverProfile | str" = DriverProfile.NORMAL,
        health_state: "HealthState | str" = HealthState.HEALTHY,
        ambient_temp: float = 25.0,
        tank_capacity_liters: float = 50.0,
        initial_fuel_percent: float = 75.0,
    ):
        if update_hz <= 0:
            raise ValueError("update_hz must be positive")
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz

        if seed is not None:
            random.seed(seed)

        # Profile / health configuration
        self.driver_profile = DriverProfile(driver_profile)
        self.profile = DRIVER_PROFILE_PARAMS[self.driver_profile]
        self.health_state = HealthState(health_state)
        self.health = HEALTH_PARAMS[self.health_state]

        # Environment / consumables
        self.ambient_temp = ambient_temp
        self.tank_capacity_l = tank_capacity_liters
        self.fuel_consumed_l = 0.0
        self._initial_fuel_fraction = initial_fuel_percent / 100.0

        # Clock / phase bookkeeping
        self.elapsed = 0.0
        self.phase = DrivePhase.IDLE
        self.phase_timer = 0.0
        self._idle_duration = random.uniform(*self.IDLE_DURATION_RANGE)
        self._city_start_duration = random.uniform(*self.CITY_START_DURATION_RANGE)

        # Vehicle state
        self.speed = 0.0
        self.throttle = 4.0
        self.rpm = 900.0
        self.coolant_temp = self.ambient_temp
        self.engine_load = 12.0
        self.fuel_rate = 0.7
        self.gear = 0
        self.distance_km = 0.0
        self._prev_throttle = 0.0
        self._last_desired_accel = 0.0
        self._power_kw = 0.0

        # Driving controller state
        self.target_speed = 0.0
        self.max_accel = 8.0 * self.profile.accel_scale
        self.max_decel = 6.0 * self.profile.decel_scale
        self._target_change_timer = 0.0

        # Aggressive-event sub-state
        self._event: Optional[str] = None
        self._event_timer = 0.0
        self._agg_stage: Optional[str] = None

        # Lead-vehicle / traffic-light car-following model
        self._lead_speed = 0.0
        self._lead_phase = "cruise"
        self._lead_cruise_target = random.uniform(*self.LEAD_CRUISE_RANGE)
        self._lead_stage_timer = 0.0
        self._next_encounter_timer = random.uniform(15.0, 35.0)
        self._lead_rate = 3.0  # current accel/decel rate for the lead vehicle

        # Gear-shift state machine
        self.current_gear = 0
        self.shift_stage: Optional[str] = None   # None | "flare" | "drop"
        self.shift_timer = 0.0
        self.shift_cooldown = 0.0
        self._accel_shift_multiplier = 1.0
        self._pre_shift_rpm = 0.0
        self._flare_target_rpm = 0.0
        self._post_shift_target_rpm = 0.0

        # Noise processes (smooth, not pure random)
        self._idle_noise = OUNoise(mu=0.0, theta=0.4, sigma=1.0)
        self._driver_noise = OUNoise(mu=0.0, theta=0.6, sigma=1.0)
        self._load_noise = OUNoise(mu=0.0, theta=0.5, sigma=1.0)
        self._stft_noise = OUNoise(mu=0.0, theta=0.5, sigma=1.0)
        self._baro_noise = OUNoise(mu=101.0, theta=0.02, sigma=0.05)
        self.short_term_fuel_trim = 0.0
        self.long_term_fuel_trim = 0.0

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _estimate_gear(self, speed: float) -> tuple[int, float]:
        for upper_bound, gear, ratio in self.GEAR_TABLE:
            if speed <= upper_bound:
                return gear, ratio
        return self.GEAR_TABLE[-1][1], self.GEAR_TABLE[-1][2]

    def _pick_new_lead_cruise_target(self) -> float:
        return random.uniform(*self.LEAD_CRUISE_RANGE)

    # ------------------------------------------------------------------ #
    # Phase / target-speed management
    # ------------------------------------------------------------------ #

    def _advance_phase_machine(self, dt: float) -> None:
        self.phase_timer += dt

        if self.phase == DrivePhase.IDLE:
            self.target_speed = 0.0
            self.max_accel = 6.0 * self.profile.accel_scale
            self.max_decel = 6.0 * self.profile.decel_scale
            if self.phase_timer >= self._idle_duration and self.coolant_temp >= 45.0:
                self.phase = DrivePhase.CITY_START
                self.phase_timer = 0.0

        elif self.phase == DrivePhase.CITY_START:
            self.max_accel = 6.0 * self.profile.accel_scale
            self.max_decel = 6.0 * self.profile.decel_scale
            ramp_target = min(40.0, self.profile.cruise_speed_range[1])
            ramp_fraction = min(1.0, self.phase_timer / self._city_start_duration)
            self.target_speed = ramp_fraction * ramp_target
            if self.phase_timer >= self._city_start_duration:
                self.phase = DrivePhase.NORMAL_CITY
                self.phase_timer = 0.0

        elif self.phase in (DrivePhase.NORMAL_CITY, DrivePhase.TRAFFIC_STOP, DrivePhase.AGGRESSIVE):
            self._run_city_event_logic(dt)

        else:
            raise RuntimeError(f"Unhandled phase: {self.phase}")

    def _run_city_event_logic(self, dt: float) -> None:
        """
        Handles NORMAL_CITY behaviour: a lead-vehicle / traffic-light
        car-following model, plus occasional driver-triggered aggressive
        accel/brake bursts that temporarily override the following behaviour.
        """
        # --- Currently mid aggressive-event: advance it ---
        if self._event == "aggressive":
            self.phase = DrivePhase.AGGRESSIVE
            if self._agg_stage == "accel":
                self.max_accel = 14.0 * self.profile.accel_scale
                self.max_decel = 8.0 * self.profile.decel_scale
                self.target_speed = min(self.speed + 35.0, self.AGGRESSIVE_TOP_SPEED)
                self._event_timer -= dt
                if self._event_timer <= 0:
                    self._agg_stage = "brake"
                    self._event_timer = random.uniform(2.5, 4.5)
            elif self._agg_stage == "brake":
                self.max_accel = 8.0 * self.profile.accel_scale
                self.max_decel = 20.0 * self.profile.decel_scale
                self.target_speed = max(self.speed - 45.0, 5.0)
                self._event_timer -= dt
                if self._event_timer <= 0:
                    self._event = None
                    self._agg_stage = None
                    self.phase = DrivePhase.NORMAL_CITY
            return

        # --- No active event: follow the lead vehicle / traffic ---
        self.max_accel = 8.0 * self.profile.accel_scale
        self.max_decel = 6.0 * self.profile.decel_scale

        self._update_lead_vehicle(dt)

        lo, hi = self.profile.cruise_speed_range
        self.target_speed = max(lo * 0.0, min(hi, self._lead_speed))  # never exceed traffic flow
        self.target_speed = max(0.0, self.target_speed)

        near_stopped = self._lead_phase in ("stopped", "holding") and self._lead_speed < 1.0
        self.phase = DrivePhase.TRAFFIC_STOP if near_stopped else DrivePhase.NORMAL_CITY

        # Random driver-triggered aggressive burst (probability scaled by profile)
        if random.random() < 0.0015 * self.profile.aggressive_event_scale * dt * self.update_hz:
            self._event = "aggressive"
            self._agg_stage = "accel"
            self._event_timer = random.uniform(3.0, 5.0)

    def _update_lead_vehicle(self, dt: float) -> None:
        """
        A lightweight car-following / traffic-light model. The lead vehicle
        cruises at a flow speed, then periodically encounters a red light,
        a pedestrian crossing, or a slow vehicle ahead - decelerating,
        holding, and re-accelerating rather than teleporting to a new speed.
        """
        if self._lead_phase == "cruise":
            self._lead_speed += max(-3.0, min(3.0, self._lead_cruise_target - self._lead_speed)) * dt
            self._next_encounter_timer -= dt
            if self._next_encounter_timer <= 0:
                roll = random.random()
                if roll < 0.45:
                    # Red traffic light: full stop, held for a while.
                    self._lead_event_target = 0.0
                    self._lead_rate = random.uniform(4.0, 7.0)
                    self._pending_hold = random.uniform(8.0, 20.0)
                elif roll < 0.70:
                    # Pedestrian crossing: quicker, shorter full stop.
                    self._lead_event_target = 0.0
                    self._lead_rate = random.uniform(6.0, 10.0)
                    self._pending_hold = random.uniform(3.0, 8.0)
                else:
                    # Slow vehicle / brief congestion: doesn't fully stop.
                    self._lead_event_target = random.uniform(8.0, 20.0)
                    self._lead_rate = random.uniform(3.0, 5.0)
                    self._pending_hold = random.uniform(3.0, 9.0)
                self._lead_phase = "decelerating"

        elif self._lead_phase == "decelerating":
            self._lead_speed -= self._lead_rate * dt
            if self._lead_speed <= self._lead_event_target:
                self._lead_speed = self._lead_event_target
                self._lead_phase = "stopped" if self._lead_event_target < 2.0 else "holding"
                self._lead_stage_timer = self._pending_hold

        elif self._lead_phase in ("stopped", "holding"):
            self._lead_stage_timer -= dt
            if self._lead_stage_timer <= 0:
                self._lead_cruise_target = self._pick_new_lead_cruise_target()
                self._lead_rate = random.uniform(3.0, 6.0)
                self._lead_phase = "accelerating"

        elif self._lead_phase == "accelerating":
            self._lead_speed += self._lead_rate * dt
            if self._lead_speed >= self._lead_cruise_target:
                self._lead_speed = self._lead_cruise_target
                self._lead_phase = "cruise"
                self._next_encounter_timer = random.uniform(15.0, 35.0)

        self._lead_speed = max(0.0, self._lead_speed)

    # ------------------------------------------------------------------ #
    # Sub-system updates
    # ------------------------------------------------------------------ #

    def _update_throttle_and_speed(self, dt: float) -> None:
        if self.phase == DrivePhase.IDLE:
            # Low, slightly unstable throttle while parked in neutral/park.
            noise = self._idle_noise.sample(dt) * self.health.idle_instability_scale
            self.throttle = max(0.0, min(15.0, 4.0 + noise * 3.0))
            self.speed = 0.0
            self._last_desired_accel = 0.0
            return

        # Proportional "driver" controller chasing the wandering target speed.
        error = self.target_speed - self.speed
        kp = 2.4 * self.profile.kp_scale
        desired_accel = kp * error
        desired_accel = max(-self.max_decel, min(self.max_accel, desired_accel))

        if desired_accel >= 0:
            throttle_target = (10.0 + desired_accel * 6.5 + self.speed * 0.15) * self.profile.throttle_gentleness
        else:
            throttle_target = 2.0

        throttle_target = max(0.0, min(100.0, throttle_target))

        # Actuator lag (throttle body / driver reaction can't jump instantly),
        # reduced further while a gear shift is interrupting torque delivery.
        lag = min(1.0, dt * self.profile.reaction_rate)
        self.throttle += (throttle_target - self.throttle) * lag
        self.throttle += self._driver_noise.sample(dt) * 1.2 * self.profile.throttle_noise_scale
        self.throttle = max(0.0, min(100.0, self.throttle))

        # Integrate speed with bounded acceleration (vehicle inertia). The
        # shift multiplier briefly reduces effective acceleration to model
        # torque interruption during an automatic-transmission gear change.
        applied_accel = desired_accel * self._accel_shift_multiplier
        self.speed += applied_accel * dt
        self.speed = max(0.0, min(self.AGGRESSIVE_TOP_SPEED, self.speed))
        self.distance_km += (self.speed * dt) / 3600.0

        self._last_desired_accel = desired_accel

    def _update_rpm(self, dt: float) -> None:
        smoothness = self.health.rpm_smoothness_scale

        if self.phase == DrivePhase.IDLE and self.speed <= 0.5:
            warmup_fraction = max(0.0, min(1.0, (self.coolant_temp - self.ambient_temp) / 45.0))
            idle_target = 1000.0 - warmup_fraction * 200.0
            noise = self._idle_noise.state * 60.0 * self.health.idle_instability_scale
            self.rpm = max(700.0, min(1100.0, idle_target + noise))
            self.gear = 0
            self.current_gear = 0
            self.shift_stage = None
            self._accel_shift_multiplier = 1.0
            return

        desired_gear, _ = self._estimate_gear(self.speed)

        if self.current_gear == 0:
            # Launching from a stop / neutral - engage directly, no flare.
            self.current_gear = desired_gear

        self.shift_cooldown = max(0.0, self.shift_cooldown - dt)

        if self.shift_stage is None and desired_gear != self.current_gear and self.shift_cooldown <= 0.0:
            if desired_gear > self.current_gear:
                # Upshift: brief RPM flare, then a sudden drop once engaged.
                self.shift_stage = "flare"
                self._pre_shift_rpm = self.rpm
                self._flare_target_rpm = min(6200.0, self.rpm + random.uniform(350.0, 650.0))
                self.shift_timer = random.uniform(0.25, 0.4)
                self._accel_shift_multiplier = 0.35
                self._pending_gear = desired_gear
            else:
                # Downshift: commit immediately, RPM rises smoothly via the
                # normal target-tracking below (no flare needed).
                self.current_gear = desired_gear

        if self.shift_stage == "flare":
            lag = min(1.0, dt * 8.0)
            self.rpm += (self._flare_target_rpm - self.rpm) * lag
            self.shift_timer -= dt
            if self.shift_timer <= 0:
                self.current_gear = self._pending_gear
                ratio = self.GEAR_RATIO_BY_NUMBER[self.current_gear]
                self._post_shift_target_rpm = max(750.0, 750.0 + self.speed * ratio + self.throttle * 14.0)
                self.shift_stage = "drop"
                self.shift_timer = random.uniform(0.15, 0.25)
                self._accel_shift_multiplier = 0.7
            self.gear = self.current_gear
            return

        if self.shift_stage == "drop":
            lag = min(1.0, dt * 10.0)
            self.rpm += (self._post_shift_target_rpm - self.rpm) * lag
            self.shift_timer -= dt
            if self.shift_timer <= 0:
                self.shift_stage = None
                self.shift_cooldown = random.uniform(1.0, 2.0)
                self._accel_shift_multiplier = 1.0
            self.gear = self.current_gear
            return

        # Steady-state tracking within the currently engaged gear.
        ratio = self.GEAR_RATIO_BY_NUMBER[self.current_gear]
        base_rpm = 750.0 + self.speed * ratio
        rev_from_throttle = self.throttle * 14.0
        target_rpm = base_rpm + rev_from_throttle

        lag = min(1.0, (dt * 5.0) / smoothness)
        self.rpm += (target_rpm - self.rpm) * lag
        if smoothness > 1.0:
            # Rougher engines add a bit of extra jitter (misfire-like roughness).
            self.rpm += random.gauss(0, 15.0 * (smoothness - 1.0))
        self.rpm = max(700.0, min(6500.0, self.rpm))
        self.gear = self.current_gear

    def _update_coolant(self, dt: float) -> None:
        offset = self.health.coolant_target_offset
        ceiling_extra = self.health.coolant_ceiling_extra

        if self.phase == DrivePhase.IDLE:
            target = 70.0 + offset * 0.5
            lag_k = 0.05
        elif self.phase == DrivePhase.TRAFFIC_STOP and self.phase_timer > 20.0:
            # Long stop with the engine idling: gentle cooling, no airflow load.
            target = 87.0 + offset
            lag_k = 0.02
        else:
            load_bonus = (self.engine_load / 100.0) * 15.0
            target = min(90.0 + load_bonus + offset, 100.0 + ceiling_extra)
            lag_k = 0.012

        self.coolant_temp += (target - self.coolant_temp) * lag_k * dt
        self.coolant_temp += random.gauss(0, 0.03)
        self.coolant_temp = max(self.ambient_temp, min(self.COOLANT_MAX, self.coolant_temp))

    def _update_engine_load_and_fuel(self, dt: float) -> None:
        rpm_fraction = self.rpm / 6500.0
        throttle_fraction = self.throttle / 100.0

        # Simple torque-curve estimate (peaks around mid-range RPM), used to
        # derive both engine load and fuel consumption consistently.
        torque_curve = max(0.2, min(1.0, 1.0 - abs(self.rpm - 3200.0) / 4500.0))
        engine_torque_nm = 170.0 * throttle_fraction * torque_curve
        self._power_kw = engine_torque_nm * self.rpm / 9549.0

        baseline_load = 12.0 + self.health.engine_load_offset
        load = baseline_load + self.throttle * 0.5 + rpm_fraction * 25.0 + self._power_kw * 0.15
        load += self._load_noise.sample(dt) * 1.5
        self.engine_load = max(0.0, min(100.0, load))

        # Deceleration fuel cut-off: modern EFI engines cut fuel almost
        # entirely on closed-throttle deceleration above idle RPM.
        decelerating_with_engine_braking = self._last_desired_accel < -0.5 and self.rpm > 1300 and self.speed > 5.0

        if self.phase == DrivePhase.IDLE or self.speed <= 0.3:
            fuel = 0.55 + rpm_fraction * 0.4
        elif decelerating_with_engine_braking:
            fuel = 0.30
        else:
            accel_enrichment = max(0.0, self.throttle - self._prev_throttle) * 0.05
            fuel = 0.5 + self._power_kw * 0.16 + rpm_fraction * 0.9 + accel_enrichment

        self.fuel_rate = max(0.25, fuel * self.health.fuel_penalty_scale)
        self._prev_throttle = self.throttle
        self.fuel_consumed_l += (self.fuel_rate * dt) / 3600.0

    def _update_extended_pids(self, dt: float) -> dict:
        """Derive additional standard OBD-II PIDs consistently from current state."""
        rpm_fraction = self.rpm / 6500.0
        throttle_fraction = self.throttle / 100.0
        noise_scale = self.health.sensor_noise_scale

        maf = max(0.3, min(90.0, (self.rpm / 1000.0) * (self.engine_load / 100.0) * 15.0))
        maf += random.gauss(0, 0.15 * noise_scale)

        battery_voltage = 14.2
        if self.rpm < 950:
            battery_voltage -= 0.4
        battery_voltage -= (self.engine_load / 100.0) * 0.3
        battery_voltage -= self.health.voltage_offset
        battery_voltage += random.gauss(0, 0.02 * noise_scale)
        battery_voltage = max(11.5, min(14.7, battery_voltage))

        heat_soak = min(18.0, (self.coolant_temp - self.ambient_temp) * 0.18)
        iat = self.ambient_temp + max(0.0, heat_soak) + random.gauss(0, 0.1 * noise_scale)

        stft = max(-15.0, min(15.0, self._stft_noise.sample(dt) * 2.0 * noise_scale))
        self.short_term_fuel_trim = stft
        self.long_term_fuel_trim += (stft - self.long_term_fuel_trim) * 0.02 * dt
        self.long_term_fuel_trim = max(-12.0, min(12.0, self.long_term_fuel_trim))

        timing_advance = max(-5.0, min(40.0, 10.0 + rpm_fraction * 22.0 - (self.engine_load / 100.0) * 12.0))
        timing_advance += random.gauss(0, 0.3 * noise_scale)

        absolute_throttle_position = max(0.0, min(100.0, self.throttle * 0.8 + 14.0))
        absolute_throttle_position += random.gauss(0, 0.2 * noise_scale)

        baro = max(97.0, min(103.0, self._baro_noise.sample(dt)))

        map_kpa = baro - (1.0 - throttle_fraction) * (baro - 32.0)
        map_kpa = max(20.0, min(baro, map_kpa)) + random.gauss(0, 0.2 * noise_scale)

        remaining_l = self.tank_capacity_l * self._initial_fuel_fraction - self.fuel_consumed_l
        fuel_level_percent = max(0.0, min(100.0, 100.0 * remaining_l / self.tank_capacity_l))

        return {
            "mass_air_flow_gps": round(maf, 2),
            "battery_voltage": round(battery_voltage, 2),
            "intake_air_temperature": round(iat, 1),
            "short_term_fuel_trim": round(stft, 2),
            "long_term_fuel_trim": round(self.long_term_fuel_trim, 2),
            "timing_advance": round(timing_advance, 1),
            "absolute_throttle_position": round(absolute_throttle_position, 1),
            "barometric_pressure": round(baro, 2),
            "intake_manifold_pressure": round(map_kpa, 1),
            "fuel_level_percent": round(fuel_level_percent, 2),
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update(self) -> Telemetry:
        """Advance the simulation by one tick (self.dt seconds) and return a snapshot."""
        dt = self.dt
        self.elapsed += dt

        self._advance_phase_machine(dt)
        self._update_throttle_and_speed(dt)
        self._update_rpm(dt)
        self._update_coolant(dt)
        self._update_engine_load_and_fuel(dt)
        extended = self._update_extended_pids(dt)

        return Telemetry(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            phase=self.phase.value,
            rpm=int(round(self.rpm)),
            speed_kmh=round(self.speed, 1),
            throttle_position=round(self.throttle, 1),
            engine_load=round(self.engine_load, 1),
            coolant_temperature=round(self.coolant_temp, 1),
            fuel_rate_lph=round(self.fuel_rate, 2),
            gear=self.gear,
            shifting=self.shift_stage is not None,
            distance_since_start_km=round(self.distance_km, 3),
            runtime_since_start_s=round(self.elapsed, 1),
            driver_profile=self.driver_profile.value,
            health_state=self.health_state.value,
            **extended,
        )

    def stream(self, duration: Optional[float] = None) -> Iterator[Telemetry]:
        """
        Generator form of the simulator, decoupled from printing/sleeping so it
        can be consumed by any backend (FastAPI websocket, SSE, message queue).
        """
        start = self.elapsed
        while duration is None or (self.elapsed - start) < duration:
            yield self.update()

    def run(self, duration: Optional[float] = None) -> None:
        """Blocking CLI-style loop: prints one JSON telemetry line per tick."""
        try:
            for reading in self.stream(duration=duration):
                print(reading.to_json())
                time.sleep(self.dt)
        except KeyboardInterrupt:
            print(json.dumps({"status": "stopped_by_user"}))


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="DriveVitals OBD-II telemetry simulator")
    parser.add_argument("--hz", type=float, default=1.0, choices=[1.0, 5.0],
                         help="Update rate in Hz (1 or 5). Default: 1")
    parser.add_argument("--duration", type=float, default=None,
                         help="Simulation duration in seconds (default: run forever)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible runs")
    parser.add_argument("--profile", type=str, default="normal",
                         choices=[p.value for p in DriverProfile],
                         help="Driver profile. Default: normal")
    parser.add_argument("--health", type=str, default="healthy",
                         choices=[h.value for h in HealthState],
                         help="Vehicle health state. Default: healthy")
    args = parser.parse_args()

    sim = OBDVehicleSimulator(
        update_hz=args.hz,
        seed=args.seed,
        driver_profile=args.profile,
        health_state=args.health,
    )
    sim.run(duration=args.duration)


if __name__ == "__main__":
    main()