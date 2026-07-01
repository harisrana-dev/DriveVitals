#!/usr/bin/env python3
"""
DriveVitals - Fleet Van Highway/City OBD-II Telemetry Simulator
=================================================================

Simulates a diesel delivery van running a multi-stop route: depot -> city
streets -> highway on-ramp -> sustained highway cruise -> city arrival ->
delivery stop (engine idling with PTO/accessory load) -> next leg, repeating
for a configurable number of legs.

Phase flow (per leg):

    DEPOT_IDLE -> CITY_DEPARTURE -> HIGHWAY_MERGE -> HIGHWAY_CRUISE
        (with sub-events: HIGHWAY_OVERTAKE, HIGHWAY_SLOWDOWN)
    -> CITY_ARRIVAL -> DELIVERY_STOP -> (next leg or ROUTE_COMPLETE)

Differences from a pure city-driving simulator:
    - Long, steady highway cruise segments (~90-120 km/h) instead of constant
      stop-and-go, with occasional overtakes (truck passing) and slowdowns
      (traffic / construction zones).
    - A "cruise_control_active" flag while holding steady highway speed.
    - Delivery stops keep the engine idling with an elevated PTO/accessory
      load (tail-lift, refrigeration unit) rather than a clean idle.
    - Diesel-appropriate RPM range (lower idle, lower cruise RPM, taller
      effective gearing) and a cumulative distance_traveled_km odometer.

Usage (standalone CLI):
    python fleet_van_highway_simulator.py --hz 1 --legs 3
    python fleet_van_highway_simulator.py --hz 5 --duration 180

Usage (embedded, e.g. FastAPI):
    sim = FleetVanOBDSimulator(update_hz=5, legs=4)
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

class RoutePhase(str, Enum):
    DEPOT_IDLE = "depot_idle"
    CITY_DEPARTURE = "city_departure"
    HIGHWAY_MERGE = "highway_merge"
    HIGHWAY_CRUISE = "highway_cruise"
    HIGHWAY_OVERTAKE = "highway_overtake"
    HIGHWAY_SLOWDOWN = "highway_slowdown"
    CITY_ARRIVAL = "city_arrival"
    DELIVERY_STOP = "delivery_stop"
    ROUTE_COMPLETE = "route_complete"


@dataclass
class VanTelemetry:
    """A single OBD-II style telemetry snapshot for the fleet van."""
    timestamp: str
    phase: str
    route_leg: int
    rpm: int
    speed_kmh: float
    throttle_position: float
    engine_load: float
    coolant_temperature: float
    fuel_rate_lph: float
    gear: int
    cruise_control_active: bool
    distance_traveled_km: float

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# --------------------------------------------------------------------------- #
# Smooth semi-random signal generator (Ornstein-Uhlenbeck process)
# --------------------------------------------------------------------------- #

class OUNoise:
    """Mean-reverting smooth random walk, used instead of raw random jitter."""

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

class FleetVanOBDSimulator:
    """
    Stateful simulator of a diesel fleet van's OBD-II telemetry across a
    multi-leg city-to-city highway route.
    """

    AMBIENT_TEMP = 22.0
    COOLANT_MAX = 104.0
    DEPOT_IDLE_DURATION_RANGE = (12.0, 20.0)
    CITY_DEPARTURE_DURATION_RANGE = (14.0, 22.0)     # ramp 0 -> ~50 km/h
    HIGHWAY_MERGE_DURATION_RANGE = (14.0, 20.0)      # ramp ~50 -> cruise speed
    HIGHWAY_CRUISE_DURATION_RANGE = (45.0, 90.0)     # sustained highway leg
    CITY_ARRIVAL_DURATION_RANGE = (20.0, 35.0)       # decelerate into city
    DELIVERY_STOP_DURATION_RANGE = (20.0, 40.0)      # engine idling, PTO load

    HIGHWAY_CRUISE_RANGE = (90.0, 120.0)
    HIGHWAY_TOP_SPEED = 132.0

    # Diesel-ish gear table: (upper_speed_bound_kmh, gear, rpm_per_kmh_in_gear)
    GEAR_TABLE = [
        (12.0, 1, 62.0),
        (25.0, 2, 40.0),
        (45.0, 3, 27.0),
        (70.0, 4, 19.0),
        (100.0, 5, 14.5),
        (999.0, 6, 11.5),
    ]

    def __init__(self, update_hz: float = 1.0, legs: int = 3, seed: Optional[int] = None):
        if update_hz <= 0:
            raise ValueError("update_hz must be positive")
        if legs < 1:
            raise ValueError("legs must be >= 1")
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz
        self.total_legs = legs

        if seed is not None:
            random.seed(seed)

        # Clock / phase bookkeeping
        self.elapsed = 0.0
        self.phase = RoutePhase.DEPOT_IDLE
        self.phase_timer = 0.0
        self.route_leg = 1
        self._depot_idle_duration = random.uniform(*self.DEPOT_IDLE_DURATION_RANGE)
        self._city_departure_duration = random.uniform(*self.CITY_DEPARTURE_DURATION_RANGE)
        self._highway_merge_duration = random.uniform(*self.HIGHWAY_MERGE_DURATION_RANGE)
        self._highway_cruise_duration = random.uniform(*self.HIGHWAY_CRUISE_DURATION_RANGE)
        self._city_arrival_duration = random.uniform(*self.CITY_ARRIVAL_DURATION_RANGE)
        self._delivery_stop_duration = random.uniform(*self.DELIVERY_STOP_DURATION_RANGE)
        self._cruise_target_speed = random.uniform(*self.HIGHWAY_CRUISE_RANGE)

        # Vehicle state
        self.speed = 0.0
        self.throttle = 5.0
        self.rpm = 780.0
        self.coolant_temp = self.AMBIENT_TEMP
        self.engine_load = 15.0
        self.fuel_rate = 1.0
        self.gear = 0
        self.distance_km = 0.0
        self.cruise_control_active = False

        # Driving controller state
        self.target_speed = 0.0
        self.max_accel = 5.0
        self.max_decel = 5.0
        self._city_target_change_timer = 0.0

        # Highway sub-event state (overtake / slowdown)
        self._highway_event: Optional[str] = None
        self._highway_event_timer = 0.0
        self._post_event_phase = RoutePhase.HIGHWAY_CRUISE

        # Noise processes (smooth, not pure random)
        self._idle_noise = OUNoise(mu=0.0, theta=0.4, sigma=1.0)
        self._driver_noise = OUNoise(mu=0.0, theta=0.5, sigma=1.0)
        self._cruise_noise = OUNoise(mu=0.0, theta=0.2, sigma=1.0)
        self._load_noise = OUNoise(mu=0.0, theta=0.5, sigma=1.0)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _estimate_gear(self, speed: float) -> tuple[int, float]:
        for upper_bound, gear, ratio in self.GEAR_TABLE:
            if speed <= upper_bound:
                return gear, ratio
        return self.GEAR_TABLE[-1][1], self.GEAR_TABLE[-1][2]

    def _start_new_leg(self) -> None:
        self.phase = RoutePhase.CITY_DEPARTURE
        self.phase_timer = 0.0
        self._city_departure_duration = random.uniform(*self.CITY_DEPARTURE_DURATION_RANGE)
        self._highway_merge_duration = random.uniform(*self.HIGHWAY_MERGE_DURATION_RANGE)
        self._highway_cruise_duration = random.uniform(*self.HIGHWAY_CRUISE_DURATION_RANGE)
        self._city_arrival_duration = random.uniform(*self.CITY_ARRIVAL_DURATION_RANGE)
        self._cruise_target_speed = random.uniform(*self.HIGHWAY_CRUISE_RANGE)

    # ------------------------------------------------------------------ #
    # Phase state machine
    # ------------------------------------------------------------------ #

    def _advance_phase_machine(self, dt: float) -> None:
        self.phase_timer += dt

        if self.phase == RoutePhase.DEPOT_IDLE:
            self.cruise_control_active = False
            self.target_speed = 0.0
            self.max_accel, self.max_decel = 4.0, 4.0
            if self.phase_timer >= self._depot_idle_duration and self.coolant_temp >= 40.0:
                self._start_new_leg()

        elif self.phase == RoutePhase.CITY_DEPARTURE:
            self.cruise_control_active = False
            self.max_accel, self.max_decel = 5.0, 5.0
            ramp = min(1.0, self.phase_timer / self._city_departure_duration)
            self.target_speed = ramp * 50.0
            if self.phase_timer >= self._city_departure_duration:
                self.phase, self.phase_timer = RoutePhase.HIGHWAY_MERGE, 0.0

        elif self.phase == RoutePhase.HIGHWAY_MERGE:
            self.cruise_control_active = False
            self.max_accel, self.max_decel = 6.5, 5.0
            ramp = min(1.0, self.phase_timer / self._highway_merge_duration)
            self.target_speed = 50.0 + ramp * (self._cruise_target_speed - 50.0)
            if self.phase_timer >= self._highway_merge_duration:
                self.phase, self.phase_timer = RoutePhase.HIGHWAY_CRUISE, 0.0

        elif self.phase in (RoutePhase.HIGHWAY_CRUISE, RoutePhase.HIGHWAY_OVERTAKE,
                             RoutePhase.HIGHWAY_SLOWDOWN):
            self._run_highway_logic(dt)

        elif self.phase == RoutePhase.CITY_ARRIVAL:
            self.cruise_control_active = False
            self.max_accel, self.max_decel = 5.0, 6.5
            self._city_target_change_timer -= dt
            if self._city_target_change_timer <= 0:
                # Decelerating stop-and-go: pick lower and lower wander targets
                progress = min(1.0, self.phase_timer / self._city_arrival_duration)
                upper = max(10.0, 45.0 * (1.0 - progress))
                self.target_speed = random.uniform(0.0, upper)
                self._city_target_change_timer = random.uniform(3.0, 6.0)
            if self.phase_timer >= self._city_arrival_duration:
                self.phase, self.phase_timer = RoutePhase.DELIVERY_STOP, 0.0
                self.target_speed = 0.0

        elif self.phase == RoutePhase.DELIVERY_STOP:
            self.cruise_control_active = False
            self.target_speed = 0.0
            self.max_accel, self.max_decel = 4.0, 4.0
            if self.phase_timer >= self._delivery_stop_duration:
                if self.route_leg >= self.total_legs:
                    self.phase, self.phase_timer = RoutePhase.ROUTE_COMPLETE, 0.0
                else:
                    self.route_leg += 1
                    self._delivery_stop_duration = random.uniform(*self.DELIVERY_STOP_DURATION_RANGE)
                    self._start_new_leg()

        elif self.phase == RoutePhase.ROUTE_COMPLETE:
            self.cruise_control_active = False
            self.target_speed = 0.0
            self.max_accel, self.max_decel = 4.0, 4.0

        else:
            raise RuntimeError(f"Unhandled phase: {self.phase}")

    def _run_highway_logic(self, dt: float) -> None:
        """Steady highway cruise with occasional overtakes and slowdowns."""

        if self._highway_event == "overtake":
            self.phase = RoutePhase.HIGHWAY_OVERTAKE
            self.cruise_control_active = False
            self.max_accel, self.max_decel = 7.0, 5.0
            self.target_speed = min(self._cruise_target_speed + 22.0, self.HIGHWAY_TOP_SPEED)
            self._highway_event_timer -= dt
            if self._highway_event_timer <= 0:
                self._highway_event = None
                self.phase, self.phase_timer = RoutePhase.HIGHWAY_CRUISE, 0.0
            return

        if self._highway_event == "slowdown":
            self.phase = RoutePhase.HIGHWAY_SLOWDOWN
            self.cruise_control_active = False
            self.max_accel, self.max_decel = 5.0, 6.0
            self.target_speed = random.uniform(55.0, 75.0)
            self._highway_event_timer -= dt
            if self._highway_event_timer <= 0:
                self._highway_event = None
                self.phase, self.phase_timer = RoutePhase.HIGHWAY_CRUISE, 0.0
            return

        # Steady cruise: small OU wander around the leg's cruise target,
        # cruise control holding speed.
        self.phase = RoutePhase.HIGHWAY_CRUISE
        self.cruise_control_active = True
        self.max_accel, self.max_decel = 4.5, 4.5
        wander = self._cruise_noise.sample(dt) * 2.5
        self.target_speed = self._cruise_target_speed + wander

        # Leg ends after the cruise duration elapses -> head into the city.
        if self.phase_timer >= self._highway_cruise_duration:
            self.cruise_control_active = False
            self.phase, self.phase_timer = RoutePhase.CITY_ARRIVAL, 0.0
            self._city_target_change_timer = 0.0
            return

        # Random overtake (passing a slower truck) or slowdown (traffic/
        # construction zone), mutually exclusive, fairly infrequent.
        if random.random() < 0.006 * dt * self.update_hz:
            self._highway_event = "overtake"
            self._highway_event_timer = random.uniform(8.0, 13.0)
        elif random.random() < 0.003 * dt * self.update_hz:
            self._highway_event = "slowdown"
            self._highway_event_timer = random.uniform(20.0, 40.0)

    # ------------------------------------------------------------------ #
    # Sub-system updates
    # ------------------------------------------------------------------ #

    def _update_throttle_and_speed(self, dt: float) -> None:
        if self.phase in (RoutePhase.DEPOT_IDLE, RoutePhase.DELIVERY_STOP, RoutePhase.ROUTE_COMPLETE):
            # PTO / accessory load bumps idle throttle slightly during a
            # delivery stop (tail-lift, refrigeration unit running).
            baseline = 6.0 if self.phase == RoutePhase.DELIVERY_STOP else 3.0
            noise = self._idle_noise.sample(dt)
            self.throttle = max(0.0, min(18.0, baseline + noise * 2.5))
            self.speed = 0.0
            return

        error = self.target_speed - self.speed
        kp = 2.0
        desired_accel = kp * error
        desired_accel = max(-self.max_decel, min(self.max_accel, desired_accel))

        if desired_accel >= 0:
            # Highway speeds need meaningfully more throttle to overcome drag.
            throttle_target = 12.0 + desired_accel * 6.0 + self.speed * 0.28
        else:
            throttle_target = 3.0

        throttle_target = max(0.0, min(100.0, throttle_target))

        lag = min(1.0, dt * 3.5)
        self.throttle += (throttle_target - self.throttle) * lag
        self.throttle += self._driver_noise.sample(dt) * 1.0
        self.throttle = max(0.0, min(100.0, self.throttle))

        self.speed += desired_accel * dt
        self.speed = max(0.0, min(self.HIGHWAY_TOP_SPEED, self.speed))
        self.distance_km += (self.speed * dt) / 3600.0

    def _update_rpm(self, dt: float) -> None:
        if self.phase in (RoutePhase.DEPOT_IDLE, RoutePhase.DELIVERY_STOP, RoutePhase.ROUTE_COMPLETE) \
                and self.speed <= 0.5:
            warmup_fraction = max(0.0, min(1.0, (self.coolant_temp - self.AMBIENT_TEMP) / 40.0))
            idle_target = 900.0 - warmup_fraction * 150.0
            if self.phase == RoutePhase.DELIVERY_STOP:
                idle_target += 90.0  # PTO / accessory load raises idle RPM
            noise = self._idle_noise.state * 40.0
            self.rpm = max(650.0, min(1000.0, idle_target + noise))
            self.gear = 0
            return

        gear, rpm_per_kmh = self._estimate_gear(self.speed)
        self.gear = gear
        base_rpm = 620.0 + self.speed * rpm_per_kmh
        rev_from_throttle = self.throttle * 9.0
        target_rpm = base_rpm + rev_from_throttle

        lag = min(1.0, dt * 4.0)
        self.rpm += (target_rpm - self.rpm) * lag
        self.rpm = max(650.0, min(4200.0, self.rpm))

    def _update_coolant(self, dt: float) -> None:
        if self.phase == RoutePhase.DEPOT_IDLE:
            target, lag_k = 68.0, 0.05
        elif self.phase == RoutePhase.DELIVERY_STOP:
            target, lag_k = 82.0, 0.02
        else:
            load_bonus = (self.engine_load / 100.0) * 12.0
            target = min(88.0 + load_bonus, 100.0)
            lag_k = 0.015

        self.coolant_temp += (target - self.coolant_temp) * lag_k * dt
        self.coolant_temp += random.gauss(0, 0.03)
        self.coolant_temp = max(self.AMBIENT_TEMP, min(self.COOLANT_MAX, self.coolant_temp))

    def _update_engine_load_and_fuel(self, dt: float) -> None:
        rpm_fraction = self.rpm / 4200.0
        baseline = 14.0
        if self.phase == RoutePhase.DELIVERY_STOP:
            baseline = 28.0  # tail-lift / reefer unit accessory draw
        load = baseline + self.throttle * 0.5 + rpm_fraction * 26.0
        load += self._load_noise.sample(dt) * 1.3
        self.engine_load = max(0.0, min(100.0, load))

        # Diesel-ish consumption: idle low, rises with load and aero drag at speed.
        drag_term = (self.speed / 100.0) ** 2 * 3.0
        self.fuel_rate = 1.0 + self.engine_load * 0.075 + rpm_fraction * 1.8 + drag_term
        self.fuel_rate = max(0.6, self.fuel_rate)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update(self) -> VanTelemetry:
        """Advance the simulation by one tick (self.dt seconds) and return a snapshot."""
        dt = self.dt
        self.elapsed += dt

        self._advance_phase_machine(dt)
        self._update_throttle_and_speed(dt)
        self._update_rpm(dt)
        self._update_coolant(dt)
        self._update_engine_load_and_fuel(dt)

        return VanTelemetry(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            phase=self.phase.value,
            route_leg=self.route_leg,
            rpm=int(round(self.rpm)),
            speed_kmh=round(self.speed, 1),
            throttle_position=round(self.throttle, 1),
            engine_load=round(self.engine_load, 1),
            coolant_temperature=round(self.coolant_temp, 1),
            fuel_rate_lph=round(self.fuel_rate, 2),
            gear=self.gear,
            cruise_control_active=self.cruise_control_active,
            distance_traveled_km=round(self.distance_km, 3),
        )

    def stream(self, duration: Optional[float] = None) -> Iterator[VanTelemetry]:
        """
        Generator form of the simulator, decoupled from printing/sleeping so
        it can be consumed by any backend (FastAPI websocket, SSE, queue).
        """
        start = self.elapsed
        while duration is None or (self.elapsed - start) < duration:
            yield self.update()
            if self.phase == RoutePhase.ROUTE_COMPLETE and self.phase_timer > 5.0:
                break

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
    parser = argparse.ArgumentParser(description="DriveVitals fleet van highway/city simulator")
    parser.add_argument("--hz", type=float, default=1.0, choices=[1.0, 5.0],
                         help="Update rate in Hz (1 or 5). Default: 1")
    parser.add_argument("--legs", type=int, default=3,
                         help="Number of city-to-city legs on the route. Default: 3")
    parser.add_argument("--duration", type=float, default=None,
                         help="Max simulation duration in seconds (default: run until route completes)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible runs")
    args = parser.parse_args()

    sim = FleetVanOBDSimulator(update_hz=args.hz, legs=args.legs, seed=args.seed)
    sim.run(duration=args.duration)


if __name__ == "__main__":
    main()