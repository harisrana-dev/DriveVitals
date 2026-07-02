"""
delivery_van_simulator.py
DriveVitals - Delivery Van OBD-II Telemetry Simulator

Simulates a fleet logistics vehicle running a multi-stop route: drive leg,
approach stop, idle at delivery, depart, repeat. Fuel-efficiency oriented
driving with cargo-load variation across the route.
"""

import argparse
import asyncio
import json
import math
import random
import time
from datetime import datetime, timezone

IDLE_RPM = 750
MAX_RPM = 4500
WHEEL_CIRCUMFERENCE_M = 2.1
FINAL_DRIVE = 4.1
GEAR_RATIOS = [4.0, 2.4, 1.6, 1.15, 0.9, 0.72]
UPSHIFT_SPEEDS = [12, 25, 40, 55, 70]
AMBIENT_TEMP = 25.0
OPERATING_TEMP = 90.0
WARMUP_TAU = 200.0
CRUISE_SPEED_CAP = 60.0
TOTAL_STOPS = 6


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
        return max(IDLE_RPM, IDLE_RPM + throttle * 2.5)
    speed_mps = speed_kmh / 3.6
    rpm = (speed_mps / WHEEL_CIRCUMFERENCE_M) * 60 * GEAR_RATIOS[gear - 1] * FINAL_DRIVE
    return min(MAX_RPM, max(IDLE_RPM, rpm))


class VehicleSimulator:
    def __init__(self, vehicle_id="FLEET-VAN-001", update_hz=5):
        self.vehicle_id = vehicle_id
        self.vehicle_type = "delivery_van"
        self.update_hz = update_hz
        self.dt = 1.0 / update_hz

        self.speed_kmh = 0.0
        self.throttle = 0.0
        self.gear = 1
        self.coolant_temp = AMBIENT_TEMP
        self.elapsed = 0.0

        self.stop_index = 0
        self.cargo_factor = 1.0  # 1.0 = full load, decreases as stops are completed

        self.phase = "driving"
        self.phase_timer = 0.0
        self._set_phase("driving", random.uniform(20, 45))

    def _set_phase(self, phase, duration):
        self.phase = phase
        self.phase_timer = duration

    def _update_cargo(self):
        # cargo lightens progressively across the route, resets on new route
        self.cargo_factor = max(0.35, 1.0 - (self.stop_index / TOTAL_STOPS) * 0.65)

    def _update_phase(self):
        self.phase_timer -= self.dt
        if self.phase_timer > 0:
            return
        if self.phase == "driving":
            self._set_phase("approaching_stop", random.uniform(4, 8))
        elif self.phase == "approaching_stop":
            self._set_phase("stopped_delivery", random.uniform(15, 45))
        elif self.phase == "stopped_delivery":
            self.stop_index = (self.stop_index + 1) % TOTAL_STOPS
            self._update_cargo()
            self._set_phase("departing", random.uniform(3, 6))
        elif self.phase == "departing":
            self._set_phase("driving", random.uniform(20, 45))

    def _target_throttle(self):
        if self.phase == "stopped_delivery":
            return 0.0
        if self.phase == "approaching_stop":
            return 0.0
        if self.phase == "departing":
            return random.uniform(30, 45)
        if self.phase == "driving":
            return random.uniform(22, 40)
        return 0.0

    def _update_dynamics(self):
        target_throttle = self._target_throttle()
        # smoother, more consistent throttle input -> eco/fuel-efficient driving
        self.throttle = ou_update(self.throttle, target_throttle, 1.8, 3.0, self.dt)
        self.throttle = min(100.0, max(0.0, self.throttle))

        load_drag = 0.05 * self.cargo_factor

        if self.phase == "approaching_stop":
            accel = -3.5
        elif self.phase == "stopped_delivery":
            accel = -6.0
        else:
            max_accel = 1.8 - (0.4 * self.cargo_factor)
            accel = (self.throttle / 100) * max_accel - load_drag

        speed_mps = max(0.0, self.speed_kmh / 3.6 + accel * self.dt)
        self.speed_kmh = min(CRUISE_SPEED_CAP, speed_mps * 3.6)

        self.gear = compute_gear(self.speed_kmh, self.gear)
        if self.speed_kmh < 1.0:
            self.gear = 1
            if self.phase in ("stopped_delivery",):
                self.speed_kmh = 0.0

    def _update_thermals(self):
        warmup_target = AMBIENT_TEMP + (OPERATING_TEMP - AMBIENT_TEMP) * (1 - math.exp(-self.elapsed / WARMUP_TAU))
        target = min(OPERATING_TEMP, warmup_target)
        if self.phase == "stopped_delivery":
            target -= 1.5  # slight cooling while idling at a stop
        self.coolant_temp = ou_update(self.coolant_temp, target, 0.04, 0.25, self.dt)
        self.coolant_temp = min(110.0, max(70.0, self.coolant_temp))

    def _compute_engine_load(self):
        load = self.throttle * 0.6 + (self.speed_kmh / CRUISE_SPEED_CAP) * 18
        load += self.cargo_factor * 8
        load += random.uniform(-3, 3)
        return min(100.0, max(0.0, load))

    def _compute_fuel_rate(self, engine_load, rpm):
        if self.phase == "stopped_delivery":
            return round(random.uniform(0.5, 0.8), 2)  # idling fuel burn
        idle_fuel = 0.85
        fuel = idle_fuel + (engine_load / 100) * 5.0 * self.cargo_factor + (rpm / MAX_RPM) * 2.0
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
    parser = argparse.ArgumentParser(description="DriveVitals Delivery Van Simulator")
    parser.add_argument("--hz", type=float, default=5)
    parser.add_argument("--duration", type=float, default=20)
    parser.add_argument("--vehicle-id", type=str, default="FLEET-VAN-001")
    args = parser.parse_args()

    sim = VehicleSimulator(vehicle_id=args.vehicle_id, update_hz=args.hz)
    for _ in range(int(args.duration * args.hz)):
        print(json.dumps(sim.step()))
        time.sleep(sim.dt)


if __name__ == "__main__":
    main()