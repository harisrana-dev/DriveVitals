"""
aggressive_driver_simulator.py
DriveVitals - Aggressive Driver OBD-II Telemetry Simulator

Same vehicle class as the city car, driven aggressively: harsh acceleration,
harsh braking, overspeeding events, and highly variable throttle input.
"""

import argparse
import asyncio
import json
import math
import random
import time
from datetime import datetime, timezone

IDLE_RPM = 800
MAX_RPM = 5000
WHEEL_CIRCUMFERENCE_M = 2.0
FINAL_DRIVE = 3.9
GEAR_RATIOS = [3.8, 2.2, 1.5, 1.1, 0.9, 0.72]
UPSHIFT_SPEEDS = [20, 40, 60, 85, 105]
AMBIENT_TEMP = 25.0
OPERATING_TEMP = 94.0
WARMUP_TAU = 140.0
NORMAL_SPEED_CAP = 65.0
OVERSPEED_CAP = 105.0


def ou_update(value, mean, theta, sigma, dt):
    return value + theta * (mean - value) * dt + sigma * math.sqrt(dt) * random.gauss(0, 1)


def compute_gear(speed_kmh, current_gear):
    if current_gear < 6 and speed_kmh > UPSHIFT_SPEEDS[current_gear - 1] + 3:
        return current_gear + 1
    if current_gear > 1 and speed_kmh < UPSHIFT_SPEEDS[current_gear - 2] - 8:
        return current_gear - 1
    return current_gear


def compute_rpm(speed_kmh, gear, throttle):
    if speed_kmh < 1.0:
        return max(IDLE_RPM, IDLE_RPM + throttle * 5.0)
    speed_mps = speed_kmh / 3.6
    rpm = (speed_mps / WHEEL_CIRCUMFERENCE_M) * 60 * GEAR_RATIOS[gear - 1] * FINAL_DRIVE
    return min(MAX_RPM, max(IDLE_RPM, rpm))


class VehicleSimulator:
    def __init__(self, vehicle_id="AGGR-CAR-001", update_hz=5):
        self.vehicle_id = vehicle_id
        self.vehicle_type = "aggressive_driver"
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz

        self.speed_kmh = 0.0
        self.throttle = 0.0
        self.gear = 1
        self.coolant_temp = AMBIENT_TEMP
        self.elapsed = 0.0

        self.phase = "idle"
        self.phase_timer = 0.0
        self._set_phase("idle", random.uniform(1, 4))

    def _set_phase(self, phase, duration):
        self.phase = phase
        self.phase_timer = duration

    def _update_phase(self):
        self.phase_timer -= self.dt
        if self.phase_timer > 0:
            return
        if self.phase == "idle":
            self._set_phase("harsh_accelerating", random.uniform(1.5, 3.5))
        elif self.phase == "harsh_accelerating":
            self._set_phase("cruising", random.uniform(2, 6))
        elif self.phase == "cruising":
            roll = random.random()
            if roll < 0.30:
                self._set_phase("overspeeding", random.uniform(3, 7))
            elif roll < 0.65:
                self._set_phase("harsh_braking", random.uniform(1, 2.5))
            else:
                self._set_phase("harsh_accelerating", random.uniform(1.5, 3.5))
        elif self.phase == "overspeeding":
            self._set_phase("harsh_braking", random.uniform(1.5, 3))
        elif self.phase == "harsh_braking":
            self._set_phase("stopped" if self.speed_kmh < 8 else "cruising", random.uniform(1, 4))
        elif self.phase == "stopped":
            self._set_phase("harsh_accelerating", random.uniform(1, 3))

    def _target_throttle(self):
        if self.phase in ("idle", "stopped", "harsh_braking"):
            return 0.0
        if self.phase == "harsh_accelerating":
            return random.uniform(75, 100)
        if self.phase == "overspeeding":
            return random.uniform(80, 100)
        if self.phase == "cruising":
            return random.uniform(20, 60)
        return 0.0

    def _update_dynamics(self):
        target_throttle = self._target_throttle()
        # high theta and sigma -> jittery, unstable throttle behavior
        self.throttle = ou_update(self.throttle, target_throttle, 3.5, 16.0, self.dt)
        self.throttle = min(100.0, max(0.0, self.throttle))

        speed_cap = OVERSPEED_CAP if self.phase == "overspeeding" else NORMAL_SPEED_CAP

        if self.phase == "harsh_braking":
            accel = -8.5
        elif self.phase == "stopped":
            accel = -7.0
        else:
            max_accel = 4.6
            accel = (self.throttle / 100) * max_accel - 0.1

        speed_mps = max(0.0, self.speed_kmh / 3.6 + accel * self.dt)
        self.speed_kmh = min(speed_cap, speed_mps * 3.6)

        self.gear = compute_gear(self.speed_kmh, self.gear)
        if self.speed_kmh < 1.0:
            self.gear = 1
            if self.phase in ("idle", "stopped"):
                self.speed_kmh = 0.0

    def _update_thermals(self):
        warmup_target = AMBIENT_TEMP + (OPERATING_TEMP - AMBIENT_TEMP) * (1 - math.exp(-self.elapsed / WARMUP_TAU))
        load_bonus = 2.0 if self.phase in ("harsh_accelerating", "overspeeding") else 0.0
        target = min(OPERATING_TEMP + load_bonus, OPERATING_TEMP + 6)
        target = max(target, warmup_target if self.elapsed < WARMUP_TAU * 2 else target)
        self.coolant_temp = ou_update(self.coolant_temp, target, 0.06, 0.5, self.dt)
        self.coolant_temp = min(110.0, max(70.0, self.coolant_temp))

    def _compute_engine_load(self):
        load = self.throttle * 0.8 + (self.speed_kmh / OVERSPEED_CAP) * 15
        load += random.uniform(-5, 5)
        return min(100.0, max(0.0, load))

    def _compute_fuel_rate(self, engine_load, rpm):
        if self.phase == "harsh_braking" and self.throttle < 5:
            return round(random.uniform(0.05, 0.2), 2)
        idle_fuel = 1.0
        fuel = idle_fuel + (engine_load / 100) * 6.5 + (rpm / MAX_RPM) * 3.5
        return round(max(0.05, fuel + random.uniform(-0.3, 0.3)), 2)

    def step(self):
        self._update_phase()
        self._update_dynamics()
        self._update_thermals()
        self.elapsed += self.dt

        rpm = compute_rpm(self.speed_kmh, self.gear, self.throttle)
        engine_load = self._compute_engine_load()
        fuel_rate = self._compute_fuel_rate(engine_load, rpm)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "phase": self.phase,
            "speed_kmh": round(self.speed_kmh, 1),
            "rpm": int(round(rpm)),
            "throttle_position": round(self.throttle, 1),
            "engine_load": round(engine_load, 1),
            "coolant_temperature": round(self.coolant_temp, 1),
            "fuel_rate_lph": fuel_rate,
            "gear": self.gear,
        }

    def stream(self):
        while True:
            yield self.step()
            time.sleep(self.dt)

    async def stream_async(self):
        while True:
            yield self.step()
            await asyncio.sleep(self.dt)


def main():
    parser = argparse.ArgumentParser(description="DriveVitals Aggressive Driver Simulator")
    parser.add_argument("--hz", type=float, default=5)
    parser.add_argument("--duration", type=float, default=20)
    parser.add_argument("--vehicle-id", type=str, default="AGGR-CAR-001")
    args = parser.parse_args()

    sim = VehicleSimulator(vehicle_id=args.vehicle_id, update_hz=args.hz)
    for _ in range(int(args.duration * args.hz)):
        print(json.dumps(sim.step()))
        time.sleep(sim.dt)


if __name__ == "__main__":
    main()