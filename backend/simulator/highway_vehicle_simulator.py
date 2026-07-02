"""
highway_vehicle_simulator.py
DriveVitals - Highway Vehicle OBD-II Telemetry Simulator

Simulates long-distance highway driving: high stable speed, cruise-control
behavior, smooth gear/RPM transitions, rare braking, occasional overtakes.
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
FINAL_DRIVE = 3.7
GEAR_RATIOS = [3.8, 2.2, 1.5, 1.1, 0.9, 0.68]
UPSHIFT_SPEEDS = [15, 30, 50, 70, 90]
AMBIENT_TEMP = 25.0
OPERATING_TEMP = 90.0
WARMUP_TAU = 120.0
CRUISE_MIN = 85.0
CRUISE_MAX = 118.0


def ou_update(value, mean, theta, sigma, dt):
    return value + theta * (mean - value) * dt + sigma * math.sqrt(dt) * random.gauss(0, 1)


def compute_gear(speed_kmh, current_gear):
    if current_gear < 6 and speed_kmh > UPSHIFT_SPEEDS[current_gear - 1] + 2:
        return current_gear + 1
    if current_gear > 1 and speed_kmh < UPSHIFT_SPEEDS[current_gear - 2] - 6:
        return current_gear - 1
    return current_gear


def compute_rpm(speed_kmh, gear, throttle):
    if speed_kmh < 1.0:
        return max(IDLE_RPM, IDLE_RPM + throttle * 3.0)
    speed_mps = speed_kmh / 3.6
    rpm = (speed_mps / WHEEL_CIRCUMFERENCE_M) * 60 * GEAR_RATIOS[gear - 1] * FINAL_DRIVE
    return min(MAX_RPM, max(IDLE_RPM, rpm))


class VehicleSimulator:
    def __init__(self, vehicle_id="HWY-VEH-001", update_hz=5):
        self.vehicle_id = vehicle_id
        self.vehicle_type = "highway_vehicle"
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz

        self.speed_kmh = 40.0
        self.throttle = 30.0
        self.gear = 4
        self.coolant_temp = AMBIENT_TEMP
        self.elapsed = 0.0

        self.cruise_target = random.uniform(CRUISE_MIN, CRUISE_MAX)
        self.phase = "merging"
        self.phase_timer = random.uniform(8, 15)

    def _set_phase(self, phase, duration):
        self.phase = phase
        self.phase_timer = duration

    def _update_phase(self):
        self.phase_timer -= self.dt
        if self.phase_timer > 0:
            return
        if self.phase == "merging":
            self._set_phase("cruising", random.uniform(30, 90))
        elif self.phase == "cruising":
            roll = random.random()
            if roll < 0.15:
                self._set_phase("overtaking", random.uniform(6, 12))
            elif roll < 0.22:
                self._set_phase("slowdown", random.uniform(8, 20))
            else:
                self.cruise_target = random.uniform(CRUISE_MIN, CRUISE_MAX)
                self._set_phase("cruising", random.uniform(30, 90))
        elif self.phase == "overtaking":
            self._set_phase("cruising", random.uniform(30, 90))
        elif self.phase == "slowdown":
            self._set_phase("cruising", random.uniform(30, 90))

    def _target_speed(self):
        if self.phase == "merging":
            return min(CRUISE_MIN, 40 + self.elapsed * 3)
        if self.phase == "overtaking":
            return min(CRUISE_MAX + 10, self.cruise_target + 18)
        if self.phase == "slowdown":
            return max(55.0, self.cruise_target - 30)
        return self.cruise_target

    def _update_dynamics(self):
        target_speed = self._target_speed()
        speed_error = target_speed - self.speed_kmh

        if self.phase == "slowdown" and speed_error < 0:
            accel = -1.2
        else:
            accel = max(-1.0, min(1.1, speed_error * 0.15))

        target_throttle = min(100.0, max(8.0, 28 + accel * 25))
        self.throttle = ou_update(self.throttle, target_throttle, 1.5, 2.0, self.dt)
        self.throttle = min(100.0, max(0.0, self.throttle))

        speed_mps = max(0.0, self.speed_kmh / 3.6 + accel * self.dt)
        self.speed_kmh = min(140.0, speed_mps * 3.6)

        self.gear = compute_gear(self.speed_kmh, self.gear)

    def _update_thermals(self):
        warmup_target = AMBIENT_TEMP + (OPERATING_TEMP - AMBIENT_TEMP) * (1 - math.exp(-self.elapsed / WARMUP_TAU))
        target = min(OPERATING_TEMP + 2, warmup_target if self.elapsed < WARMUP_TAU * 2 else OPERATING_TEMP + 2)
        self.coolant_temp = ou_update(self.coolant_temp, target, 0.04, 0.2, self.dt)
        self.coolant_temp = min(110.0, max(70.0, self.coolant_temp))

    def _compute_engine_load(self):
        load = self.throttle * 0.55 + (self.speed_kmh / 120) * 25
        load += random.uniform(-2, 2)
        return min(100.0, max(0.0, load))

    def _compute_fuel_rate(self, engine_load, rpm):
        idle_fuel = 0.9
        fuel = idle_fuel + (engine_load / 100) * 5.5 + (rpm / MAX_RPM) * 2.5
        return round(max(0.1, fuel + random.uniform(-0.15, 0.15)), 2)

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
    parser = argparse.ArgumentParser(description="DriveVitals Highway Vehicle Simulator")
    parser.add_argument("--hz", type=float, default=5)
    parser.add_argument("--duration", type=float, default=20)
    parser.add_argument("--vehicle-id", type=str, default="HWY-VEH-001")
    args = parser.parse_args()

    sim = VehicleSimulator(vehicle_id=args.vehicle_id, update_hz=args.hz)
    for _ in range(int(args.duration * args.hz)):
        print(json.dumps(sim.step()))
        time.sleep(sim.dt)


if __name__ == "__main__":
    main()