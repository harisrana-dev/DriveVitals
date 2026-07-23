#!/usr/bin/env python
"""
Fleet Runtime Demo

Runs a multi-vehicle fleet through FleetRunner and prints a live
dashboard of every TelemetrySample until all trips complete.

Usage:
    python scripts/run_fleet_demo.py
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Ensure backend/ is on sys.path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver, BehaviorProfile
from backend.fleet.models.route import Route, RouteType
from backend.fleet.models.trip import Trip
from backend.fleet.models.vehicle import Vehicle, EngineStatus
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.telemetry.models.telemetry_sample import TelemetrySample


# ── Fleet definition ──────────────────────────────────────────────

VEHICLES = [
    Vehicle(vehicle_id="V-101", make="Ford", model="Transit", year=2023,
            odometer_km=14230.5, fuel_level_percent=87.0),
    Vehicle(vehicle_id="V-102", make="Mercedes", model="Sprinter", year=2024,
            odometer_km=8912.0, fuel_level_percent=95.0),
    Vehicle(vehicle_id="V-103", make="RAM", model="ProMaster", year=2022,
            odometer_km=52103.7, fuel_level_percent=62.0),
]

DRIVERS = [
    Driver(driver_id="D-01", name="Alice Chen", behavior_profile=BehaviorProfile.AGGRESSIVE),
    Driver(driver_id="D-02", name="Bob Park", behavior_profile=BehaviorProfile.ECO),
    Driver(driver_id="D-03", name="Carol Diaz", behavior_profile=BehaviorProfile.STANDARD),
]

ROUTES = [
    Route(route_id="R-01", origin="Warehouse A", destination="Customer Alpha",
          distance_km=5.0, route_type=RouteType.URBAN, speed_limit_kmh=60.0),
    Route(route_id="R-02", origin="Warehouse B", destination="Customer Bravo",
          distance_km=12.0, route_type=RouteType.HIGHWAY, speed_limit_kmh=110.0),
    Route(route_id="R-03", origin="Depot", destination="Customer Charlie",
          distance_km=3.5, route_type=RouteType.URBAN, speed_limit_kmh=50.0),
]


# ── Dashboard rendering ───────────────────────────────────────────

_HEADER = "\033[1m\033[36m"
_RESET = "\033[0m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_DIM = "\033[2m"

_TRIP_SYMBOLS = {
    "assigned": f"{_YELLOW}●{_RESET}",
    "started": f"{_YELLOW}◉{_RESET}",
    "in_progress": f"{_GREEN}◉{_RESET}",
    "completed": f"{_DIM}✓{_RESET}",
}


def _bar(value: float, width: int = 15, fill: str = "█", empty: str = "░") -> str:
    filled = int(value / 100.0 * width)
    return fill * filled + empty * (width - filled)


def _speed_color(speed: float, limit: float) -> str:
    ratio = speed / limit if limit > 0 else 0
    if ratio > 1.1:
        return _RED
    if ratio > 0.9:
        return _YELLOW
    return _GREEN


def _print_dashboard(
    samples: list[TelemetrySample],
    vehicles: list[Vehicle],
    trips: list[Trip],
    tick: int,
    elapsed: timedelta,
) -> None:
    """Print a single dashboard frame to stdout."""
    # Move cursor up and overwrite previous frame (except first tick).
    if tick > 0:
        lines = 3 + len(vehicles) * 6 + 2
        sys.stdout.write(f"\033[{lines}A")
        sys.stdout.write("\033[J")

    now_str = (datetime(2025, 1, 15, 8, 0, 0) + elapsed).strftime("%H:%M:%S")
    print(f"{_HEADER}═══ DriveVitals Fleet Demo ═══{_RESET}  tick {tick:>3}  sim {now_str}")
    print()

    # Build a lookup of the latest sample per vehicle.
    latest_by_vid: dict[str, TelemetrySample] = {}
    for s in samples:
        latest_by_vid[s.vehicle_id] = s

    for vehicle, trip in zip(vehicles, trips):
        s = latest_by_vid.get(vehicle.vehicle_id)
        status_sym = _TRIP_SYMBOLS.get(trip.status.value, "?")

        # Identity line.
        print(
            f"  {status_sym} "
            f"{_HEADER}{vehicle.vehicle_id}{_RESET}  "
            f"{trip.driver_id}  "
            f"{_DIM}{trip.route_id}{_RESET}  "
            f"{_DIM}{trip.status.value}{_RESET}"
        )

        if s is None:
            print(f"    {_DIM}waiting for first telemetry...{_RESET}")
            print()
            continue

        # Speed bar.
        limit = 60.0  # shown as reference; actual varies per route.
        for r in ROUTES:
            if r.route_id == trip.route_id:
                limit = r.speed_limit_kmh
                break
        spd_color = _speed_color(s.speed_kmh, limit)
        speed_bar = _bar(min(s.speed_kmh / limit * 100, 100), width=20)
        print(
            f"    Speed   {spd_color}{s.speed_kmh:>6.1f}{_RESET} km/h  "
            f"[{spd_color}{speed_bar}{_RESET}]  limit {limit:.0f}"
        )

        # Fuel bar.
        fuel_color = _GREEN if s.fuel_level_percent > 20 else _YELLOW if s.fuel_level_percent > 10 else _RED
        fuel_bar = _bar(s.fuel_level_percent, width=20)
        print(
            f"    Fuel    {fuel_color}{s.fuel_level_percent:>5.1f}{_RESET} %   "
            f"[{fuel_color}{fuel_bar}{_RESET}]"
        )

        # RPM, coolant, odometer on one line.
        print(
            f"    RPM {s.rpm:>6.0f}  "
            f"Coolant {s.coolant_temperature_c:>5.1f}°C  "
            f"Odometer {s.odometer_km:>8.1f} km  "
            f"Trip {trip.distance_travelled_km:.2f}/{trip.route_id}"
        )
        print()


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    start_time = datetime(2025, 1, 15, 8, 0, 0)
    tick_seconds = 1.0

    # Build fleet.
    fleet = FleetRunner(tick_seconds=tick_seconds)
    for v, d, r in zip(VEHICLES, DRIVERS, ROUTES):
        assignment = Assignment(
            assignment_id=f"A-{v.vehicle_id}",
            driver_id=d.driver_id,
            vehicle_id=v.vehicle_id,
            route_id=r.route_id,
        )
        trip = Trip(
            trip_id=f"T-{v.vehicle_id}",
            vehicle_id=v.vehicle_id,
            driver_id=d.driver_id,
            route_id=r.route_id,
        )
        fleet.add_assignment(
            assignment=assignment, vehicle=v, driver=d, route=r, trip=trip,
        )

    print(f"\033[2J\033[H", end="")  # Clear screen.

    all_samples: list[TelemetrySample] = []
    now = start_time
    tick = 0

    fleet.start_all(now=now)

    while fleet.active_runners():
        for sample in fleet.tick_all(now=now):
            all_samples.append(sample)
        now = now + timedelta(seconds=tick_seconds)
        tick += 1

        _print_dashboard(all_samples, VEHICLES, [fleet._runners[i].trip for i in range(len(fleet._runners))], tick, now - start_time)
        time.sleep(0.15)  # Pace the output so it's readable.

    # Final summary.
    print(f"{_HEADER}═══ All trips completed ═══{_RESET}")
    print()
    for v, d, r in zip(VEHICLES, DRIVERS, ROUTES):
        trip = [run.trip for run in fleet._runners if run.vehicle.vehicle_id == v.vehicle_id][0]
        fuel_used = (87.0 if v.vehicle_id == "V-101" else 95.0 if v.vehicle_id == "V-102" else 62.0) - v.fuel_level_percent
        print(
            f"  {v.vehicle_id}  {d.name:<14}  "
            f"distance {trip.distance_travelled_km:.2f} km  "
            f"fuel used {fuel_used:.2f}%  "
            f"odometer {v.odometer_km:.1f} km"
        )
    print()


if __name__ == "__main__":
    main()
