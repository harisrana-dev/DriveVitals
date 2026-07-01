#!/usr/bin/env python3
"""
DriveVitals - OBD-II Vehicle Telemetry Simulator
=================================================

Simulates a gasoline city car driving through realistic phases:

    IDLE -> CITY_START -> NORMAL_CITY (with TRAFFIC_STOP / AGGRESSIVE events)

The simulator is physics-inspired, not random-noise-driven:
    - Speed has inertia (bounded acceleration / deceleration, not teleporting).
    - RPM is derived from speed, estimated gear, and throttle position.
    - Coolant temperature warms up asymptotically toward a load-dependent target.
    - Throttle is produced by a simple proportional "driver" controller reacting
      to a wandering target speed, smoothed through an actuator lag, plus a
      small Ornstein-Uhlenbeck noise term for human imprecision (NOT pure noise).

Usage (standalone CLI):
    python drivevitals_simulator.py --hz 1
    python drivevitals_simulator.py --hz 5 --duration 120

Usage (embedded, e.g. in FastAPI):
    sim = OBDVehicleSimulator(update_hz=5)
    for telemetry in sim.stream():
        await websocket.send_json(telemetry.to_dict())

FastAPI sketch:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    import json, asyncio

    app = FastAPI()

    @app.get("/telemetry/stream")
    async def telemetry_stream():
        sim = OBDVehicleSimulator(update_hz=5)

        async def event_source():
            for reading in sim.stream():
                yield f"data: {reading.to_json()}\n\n"
                await asyncio.sleep(sim.dt)

        return StreamingResponse(event_source(), media_type="text/event-stream")
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


@dataclass
class Telemetry:
    """A single OBD-II style telemetry snapshot."""
    timestamp: str
    phase: str
    rpm: int
    speed_kmh: float
    throttle_position: float
    engine_load: float
    coolant_temperature: float
    fuel_rate_lph: float
    gear: int

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
    AMBIENT_TEMP = 25.0
    COOLANT_MAX = 108.0
    IDLE_DURATION_RANGE = (18.0, 30.0)          # seconds warming up at idle
    CITY_START_DURATION_RANGE = (18.0, 28.0)    # seconds ramping 0 -> ~40 km/h
    NORMAL_SPEED_RANGE = (20.0, 60.0)
    AGGRESSIVE_TOP_SPEED = 85.0

    # Gear table: (upper_speed_bound_kmh, rpm_per_kmh_in_gear)
    GEAR_TABLE = [
        (15.0, 1, 128.0),
        (30.0, 2, 82.0),
        (48.0, 3, 58.0),
        (68.0, 4, 42.0),
        (999.0, 5, 32.0),
    ]

    def __init__(self, update_hz: float = 1.0, seed: Optional[int] = None):
        if update_hz <= 0:
            raise ValueError("update_hz must be positive")
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz

        if seed is not None:
            random.seed(seed)

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
        self.coolant_temp = self.AMBIENT_TEMP
        self.engine_load = 12.0
        self.fuel_rate = 0.7
        self.gear = 0

        # Driving controller state
        self.target_speed = 0.0
        self.max_accel = 8.0     # km/h per second
        self.max_decel = 6.0     # km/h per second (comfort braking)
        self._target_change_timer = 0.0

        # Event sub-state machine (traffic stops / aggressive bursts)
        self._event: Optional[str] = None
        self._event_timer = 0.0
        self._agg_stage: Optional[str] = None

        # Noise processes (smooth, not pure random)
        self._idle_noise = OUNoise(mu=0.0, theta=0.4, sigma=1.0)
        self._driver_noise = OUNoise(mu=0.0, theta=0.6, sigma=1.0)
        self._load_noise = OUNoise(mu=0.0, theta=0.5, sigma=1.0)

    # ------------------------------------------------------------------ #
    # Phase / target-speed management
    # ------------------------------------------------------------------ #

    def _estimate_gear(self, speed: float) -> tuple[int, float]:
        for upper_bound, gear, ratio in self.GEAR_TABLE:
            if speed <= upper_bound:
                return gear, ratio
        return self.GEAR_TABLE[-1][1], self.GEAR_TABLE[-1][2]

    def _pick_new_normal_target(self) -> float:
        lo, hi = self.NORMAL_SPEED_RANGE
        return random.uniform(lo, hi)

    def _advance_phase_machine(self, dt: float) -> None:
        self.phase_timer += dt

        if self.phase == DrivePhase.IDLE:
            self.target_speed = 0.0
            self.max_accel, self.max_decel = 6.0, 6.0
            if self.phase_timer >= self._idle_duration and self.coolant_temp >= 45.0:
                self.phase = DrivePhase.CITY_START
                self.phase_timer = 0.0

        elif self.phase == DrivePhase.CITY_START:
            self.max_accel, self.max_decel = 6.0, 6.0
            ramp_fraction = min(1.0, self.phase_timer / self._city_start_duration)
            self.target_speed = ramp_fraction * 40.0
            if self.phase_timer >= self._city_start_duration:
                self.phase = DrivePhase.NORMAL_CITY
                self.phase_timer = 0.0
                self._target_change_timer = random.uniform(4.0, 9.0)
                self.target_speed = self._pick_new_normal_target()

        elif self.phase in (DrivePhase.NORMAL_CITY, DrivePhase.TRAFFIC_STOP, DrivePhase.AGGRESSIVE):
            self._run_city_event_logic(dt)

        else:
            raise RuntimeError(f"Unhandled phase: {self.phase}")

    def _run_city_event_logic(self, dt: float) -> None:
        """
        Handles the NORMAL_CITY behaviour: wandering target speed, random
        traffic-light stops, and occasional aggressive accel/brake bursts.
        """
        # --- Currently mid-event: advance it ---
        if self._event == "stop":
            self.phase = DrivePhase.TRAFFIC_STOP
            self.max_accel, self.max_decel = 6.0, 7.0
            self.target_speed = 0.0
            self._event_timer -= dt
            if self._event_timer <= 0:
                self._event = None
                self.phase = DrivePhase.NORMAL_CITY
                self._target_change_timer = random.uniform(3.0, 7.0)
                self.target_speed = self._pick_new_normal_target()
            return

        if self._event == "aggressive":
            self.phase = DrivePhase.AGGRESSIVE
            if self._agg_stage == "accel":
                self.max_accel, self.max_decel = 14.0, 8.0
                self.target_speed = min(self.speed + 35.0, self.AGGRESSIVE_TOP_SPEED)
                self._event_timer -= dt
                if self._event_timer <= 0:
                    self._agg_stage = "brake"
                    self._event_timer = random.uniform(2.5, 4.5)
            elif self._agg_stage == "brake":
                self.max_accel, self.max_decel = 8.0, 20.0
                self.target_speed = max(self.speed - 45.0, 5.0)
                self._event_timer -= dt
                if self._event_timer <= 0:
                    self._event = None
                    self._agg_stage = None
                    self.phase = DrivePhase.NORMAL_CITY
                    self._target_change_timer = random.uniform(4.0, 8.0)
                    self.target_speed = self._pick_new_normal_target()
            return

        # --- No active event: normal wandering + chance to trigger one ---
        self.phase = DrivePhase.NORMAL_CITY
        self.max_accel, self.max_decel = 8.0, 6.0

        self._target_change_timer -= dt
        if self._target_change_timer <= 0:
            self.target_speed = self._pick_new_normal_target()
            self._target_change_timer = random.uniform(4.0, 9.0)

        # Random traffic-light stop (~ once every couple of minutes on average)
        if random.random() < 0.004 * dt * self.update_hz:
            self._event = "stop"
            self._event_timer = random.uniform(5.0, 14.0)
            return

        # Random aggressive burst (rarer)
        if random.random() < 0.0015 * dt * self.update_hz:
            self._event = "aggressive"
            self._agg_stage = "accel"
            self._event_timer = random.uniform(3.0, 5.0)
            return

    # ------------------------------------------------------------------ #
    # Sub-system updates
    # ------------------------------------------------------------------ #

    def _update_throttle_and_speed(self, dt: float) -> None:
        if self.phase == DrivePhase.IDLE:
            # Low, slightly unstable throttle while parked in neutral/park.
            noise = self._idle_noise.sample(dt)
            self.throttle = max(0.0, min(15.0, 4.0 + noise * 3.0))
            self.speed = 0.0
            return

        # Proportional "driver" controller chasing the wandering target speed.
        error = self.target_speed - self.speed
        kp = 2.4
        desired_accel = kp * error
        desired_accel = max(-self.max_decel, min(self.max_accel, desired_accel))

        if desired_accel >= 0:
            throttle_target = 10.0 + desired_accel * 6.5 + self.speed * 0.15
        else:
            # Braking: engine throttle drops toward idle regardless of decel force.
            throttle_target = 2.0

        throttle_target = max(0.0, min(100.0, throttle_target))

        # Actuator lag (throttle body / driver reaction can't jump instantly)
        lag = min(1.0, dt * 4.0)
        self.throttle += (throttle_target - self.throttle) * lag
        self.throttle += self._driver_noise.sample(dt) * 1.2
        self.throttle = max(0.0, min(100.0, self.throttle))

        # Integrate speed with bounded acceleration (vehicle inertia)
        self.speed += desired_accel * dt
        self.speed = max(0.0, min(self.AGGRESSIVE_TOP_SPEED, self.speed))

    def _update_rpm(self, dt: float) -> None:
        if self.phase == DrivePhase.IDLE and self.speed <= 0.5:
            # Cold engines idle a bit higher than warm ones.
            warmup_fraction = max(0.0, min(1.0, (self.coolant_temp - self.AMBIENT_TEMP) / 45.0))
            idle_target = 1000.0 - warmup_fraction * 200.0
            noise = self._idle_noise.state * 60.0
            self.rpm = max(700.0, min(1100.0, idle_target + noise))
            self.gear = 0
            return

        gear, rpm_per_kmh = self._estimate_gear(self.speed)
        self.gear = gear
        base_rpm = 750.0 + self.speed * rpm_per_kmh
        rev_from_throttle = self.throttle * 14.0  # revving before an upshift
        target_rpm = base_rpm + rev_from_throttle

        # RPM tracks its target quickly but not instantaneously (drivetrain lag)
        lag = min(1.0, dt * 5.0)
        self.rpm += (target_rpm - self.rpm) * lag
        self.rpm = max(700.0, min(6500.0, self.rpm))

    def _update_coolant(self, dt: float) -> None:
        if self.phase == DrivePhase.IDLE:
            target = 70.0
            lag_k = 0.05  # 1/s -> ~20s time constant while warming up at idle
        else:
            load_bonus = (self.engine_load / 100.0) * 15.0
            target = min(90.0 + load_bonus, 105.0)
            lag_k = 0.02  # 1/s -> slower approach toward operating temperature

        # First-order lag toward the target temperature, in real seconds (dt),
        # so behaviour is consistent regardless of update_hz.
        self.coolant_temp += (target - self.coolant_temp) * lag_k * dt
        self.coolant_temp += random.gauss(0, 0.03)  # tiny thermal jitter
        self.coolant_temp = max(self.AMBIENT_TEMP, min(self.COOLANT_MAX, self.coolant_temp))

    def _update_engine_load_and_fuel(self, dt: float) -> None:
        rpm_fraction = self.rpm / 6500.0
        baseline = 12.0
        load = baseline + self.throttle * 0.55 + rpm_fraction * 28.0
        load += self._load_noise.sample(dt) * 1.5
        self.engine_load = max(0.0, min(100.0, load))

        self.fuel_rate = 0.7 + self.engine_load * 0.09 + rpm_fraction * 2.6
        self.fuel_rate = max(0.5, self.fuel_rate)

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
    args = parser.parse_args()

    sim = OBDVehicleSimulator(update_hz=args.hz, seed=args.seed)
    sim.run(duration=args.duration)


if __name__ == "__main__":
    main()
