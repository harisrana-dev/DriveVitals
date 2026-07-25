#!/usr/bin/env python
"""
DriveVitals Raw Fleet Telemetry Demo.

Runs multiple configured vehicles and drivers through the fleet runtime
and prints every generated TelemetrySample as it is produced.

Usage:
    python scripts/run_fleet_telemetry.py
"""

from datetime import datetime, timedelta
import time


# Ensure backend/ is importable.


from backend.fleet.config.fleet_factory import FleetFactory
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.telemetry.models.telemetry_sample import TelemetrySample
from backend.fleet.models.trip import Trip
from backend.pipeline.telemetry_pipeline import TelemetryPipeline
from backend.analytics.engine import AnalyticsEngine

def print_telemetry(sample: TelemetrySample) -> None:
    """
    Print one complete telemetry packet.

    This represents the raw telemetry stream that would eventually
    be consumed by the analytics layer.
    """

    print(
        f"\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"TIMESTAMP       : {sample.timestamp}\n"
        f"VEHICLE         : {sample.vehicle_id}\n"
        f"DRIVER          : {sample.driver_id}\n"
        f"TRIP            : {sample.trip_id}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"SPEED           : {sample.speed_kmh:>8.2f} km/h\n"
        f"RPM             : {sample.rpm:>8.0f}\n"
        f"THROTTLE        : {sample.throttle_position_percent:>8.1f} %\n"
        f"BRAKE PRESSURE  : {sample.brake_pressure:>8.2f}\n"
        f"COOLANT TEMP    : {sample.coolant_temperature_c:>8.1f} °C\n"
        f"ENGINE LOAD     : {sample.engine_load_percent:>8.1f} %\n"
        f"FUEL RATE       : {sample.fuel_rate_lph:>8.2f} L/h\n"
        f"FUEL LEVEL      : {sample.fuel_level_percent:>8.2f} %\n"
        f"ODOMETER        : {sample.odometer_km:>8.2f} km\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


def main() -> None:
    start_time = datetime(2025, 1, 15, 8, 0, 0)
    tick_seconds = 1.0

    # Load the entire fleet from fleet_config.py.
    configured_fleet = FleetFactory.from_config()

    fleet = FleetRunner(
        tick_seconds=tick_seconds,
    )
    pipeline = TelemetryPipeline()
    analytics_engine = AnalyticsEngine()
    pipeline.register(analytics_engine)

    # Add every configured assignment to the runtime.
    for assignment in configured_fleet.assignments:

        vehicle = next(
            v for v in configured_fleet.vehicles
            if v.vehicle_id == assignment.vehicle_id
        )

        driver = next(
            d for d in configured_fleet.drivers
            if d.driver_id == assignment.driver_id
        )

        route = next(
            r for r in configured_fleet.routes
            if r.route_id == assignment.route_id
        )

        trip = Trip(
            trip_id=f"T-{assignment.assignment_id}",
            vehicle_id=vehicle.vehicle_id,
            driver_id=driver.driver_id,
            route_id=route.route_id,
        )

        fleet.add_assignment(
            assignment=assignment,
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )

    print("\033[2J\033[H", end="")

    print("════════════════════════════════════════════════════════════")
    print("              DriveVitals Raw Telemetry Stream")
    print("════════════════════════════════════════════════════════════")
    print()

    now = start_time
    tick = 0

    fleet.start_all(now=now)

    while fleet.active_runners():

        print(
            f"\n\n"
            f"==================== TICK {tick} ====================\n"
            f"SIMULATION TIME: {now}"
        )

        samples = fleet.tick_all(now=now)

        for sample in samples:
            print_telemetry(sample)
            pipeline.publish(sample)

        now = now + timedelta(seconds=tick_seconds)
        time.sleep(tick_seconds)

    print()
    print("════════════════════════════════════════════════════════════")
    print("                 ALL TRIPS COMPLETED")
    print("════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()