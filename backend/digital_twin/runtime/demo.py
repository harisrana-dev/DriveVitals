"""Demonstration of the Continuous Digital Twin Runtime.

Shows the runtime executing the full pipeline:
Physics → Sensors → Telemetry → Analytics

Run in real-time mode (default) or accelerated mode (--fast).

Usage:
    python -m digital_twin.runtime.demo
    python -m digital_twin.runtime.demo --fast
    python -m digital_twin.runtime.demo --ticks 20
"""

from __future__ import annotations

import sys
import time
from datetime import datetime

from digital_twin.common.enums import VehicleStatus
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.runtime.continuous_runtime import ContinuousRuntime


def create_demo_vehicles(count: int = 3) -> list[Vehicle]:
    """Create demo vehicles with realistic specifications."""
    vehicles = []
    specs = [
        ("Ford", "Transit", 2022, FuelType.DIESEL, TransmissionType.AUTOMATIC),
        ("Mercedes", "Sprinter", 2023, FuelType.DIESEL, TransmissionType.AUTOMATIC),
        ("Iveco", "Daily", 2021, FuelType.DIESEL, TransmissionType.MANUAL),
    ]
    for i in range(1, count + 1):
        manufacturer, model, year, fuel, trans = specs[(i - 1) % len(specs)]
        vehicle = Vehicle(
            vehicle_id=f"vehicle-{i:03d}",
            vin=f"VIN{2024000000 + i:010d}",
            specification=VehicleSpecification(
                manufacturer=manufacturer,
                model=model,
                year=year,
                fuel_type=fuel,
                transmission=trans,
            ),
            status=VehicleStatus.AVAILABLE,
        )
        vehicles.append(vehicle)
    return vehicles


def print_tick_summary(result, vehicles_processed: int) -> None:
    """Print a concise tick summary."""
    # Count events across all vehicles
    total_events = 0
    for vtr in result.vehicle_results.values():
        if vtr.analytics_result and "events" in vtr.analytics_result:
            total_events += len(vtr.analytics_result["events"])

    time_str = result.simulation_time.strftime("%H:%M:%S")
    print(
        f"TICK {result.tick_id:4d} | "
        f"SIMULATION TIME {time_str} | "
        f"Vehicles: {vehicles_processed} | "
        f"Analytics processed: {len(result.vehicle_results)} | "
        f"Events: {total_events}"
    )


def main() -> None:
    """Run the demonstration."""
    # Parse arguments
    fast_mode = "--fast" in sys.argv
    num_ticks = 10
    for i, arg in enumerate(sys.argv):
        if arg == "--ticks" and i + 1 < len(sys.argv):
            num_ticks = int(sys.argv[i + 1])

    print("=" * 70)
    print("DIGITAL TWIN CONTINUOUS RUNTIME DEMONSTRATION")
    print("=" * 70)
    print(f"Mode: {'ACCELERATED' if fast_mode else 'REAL-TIME'}")
    print(f"Ticks: {num_ticks}")
    print()

    # Create runtime
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)

    # Add vehicles
    vehicles = create_demo_vehicles(3)
    for vehicle in vehicles:
        runtime.add_vehicle(vehicle)

    print(f"Registered {len(vehicles)} vehicles:")
    for v in vehicles:
        spec = v.specification
        print(f"  - {v.vehicle_id}: {spec.manufacturer} {spec.model} ({spec.year})")
    print()

    # Start runtime
    runtime.start()
    print("Runtime STARTED")
    print("-" * 70)

    # Run simulation
    start_time = time.perf_counter()

    if fast_mode:
        # Accelerated: run all ticks as fast as possible
        f = io.StringIO() if "--quiet" in sys.argv else None
        import io
        if f:
            with contextlib.redirect_stdout(f):
                runtime.run(num_ticks=num_ticks, real_time=False)
        else:
            runtime.run(num_ticks=num_ticks, real_time=False)

        # Print summary of last tick
        # Re-run a few ticks to get fresh results for printing
        runtime.reset()
        runtime.start()
        for _ in range(min(num_ticks, 5)):
            result = runtime.step()
            print_tick_summary(result, len(vehicles))
    else:
        # Real-time: print each tick
        import contextlib
        for _ in range(num_ticks):
            result = runtime.step()
            print_tick_summary(result, len(vehicles))
            # The runtime already handles real-time pacing in run()
            # For manual stepping, we add a small delay
            time.sleep(0.1)

    elapsed = time.perf_counter() - start_time

    print("-" * 70)
    print(f"Runtime STOPPED after {runtime.tick_id} ticks ({elapsed:.2f}s wall-clock)")
    print()

    # Print final vehicle states
    print("FINAL VEHICLE STATES:")
    for vehicle in vehicles:
        state = vehicle.state
        print(
            f"  {vehicle.vehicle_id}: "
            f"speed={state.current_speed_kmh:.1f} km/h | "
            f"rpm={state.current_rpm:.0f} | "
            f"fuel={state.fuel_level_percent:.1f}% | "
            f"odometer={state.odometer_km:.3f} km | "
            f"engine_hours={state.engine_hours:.4f} h"
        )

    print()
    print("Demonstration complete.")


if __name__ == "__main__":
    main()
