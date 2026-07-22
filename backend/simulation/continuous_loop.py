"""Continuous simulation loop: thin orchestration around the existing Digital Twin.

Runs one tick per real-time second, prints raw telemetry and analytics
for each vehicle.

Usage:
    cd backend
    python -m simulation.continuous_loop
"""

import time
import sys

from analytics.engine import AnalyticsEngine
from digital_twin.common.enums import VehicleStatus
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.runtime.continuous_runtime import ContinuousRuntime
from digital_twin.sensors.sensor_models import NumericSensorReading


def create_vehicles(count: int = 3) -> list[Vehicle]:
    """Create demo vehicles."""
    specs = [
        ("Ford", "Transit", 2022, FuelType.DIESEL, TransmissionType.AUTOMATIC),
        ("Mercedes", "Sprinter", 2023, FuelType.DIESEL, TransmissionType.AUTOMATIC),
        ("Iveco", "Daily", 2021, FuelType.DIESEL, TransmissionType.MANUAL),
    ]
    vehicles = []
    for i in range(1, count + 1):
        m, md, yr, ft, tr = specs[(i - 1) % len(specs)]
        vehicles.append(Vehicle(
            vehicle_id=f"vehicle-{i:03d}",
            vin=f"VIN{2024000000 + i:010d}",
            specification=VehicleSpecification(
                manufacturer=m, model=md, year=yr,
                fuel_type=ft, transmission=tr,
            ),
            status=VehicleStatus.AVAILABLE,
        ))
    return vehicles


def extract_sensor_value(packet, sensor_name: str) -> float | None:
    """Extract a numeric value from a TelemetryPacket by sensor name."""
    for reading in packet.sensor_readings:
        if reading.sensor_name == sensor_name and isinstance(reading, NumericSensorReading):
            return reading.value
    return None


def print_telemetry(vehicle_id: str, packet) -> None:
    """Print raw telemetry from a TelemetryPacket."""
    speed = extract_sensor_value(packet, "vehicle_speed")
    rpm = extract_sensor_value(packet, "engine_rpm")
    gear = extract_sensor_value(packet, "gear_position")
    fuel = extract_sensor_value(packet, "fuel_level")
    engine_load = extract_sensor_value(packet, "engine_load")
    engine_temp = extract_sensor_value(packet, "engine_temperature")
    battery = extract_sensor_value(packet, "battery_voltage")
    odometer = extract_sensor_value(packet, "odometer")
    brake = extract_sensor_value(packet, "brake_pad_health")
    tyre = extract_sensor_value(packet, "tyre_health")

    print(f"VEHICLE: {vehicle_id}")
    print("RAW TELEMETRY")
    print(f"  speed: {speed if speed is not None else 'N/A'} km/h")
    print(f"  rpm: {rpm if rpm is not None else 'N/A'}")
    print(f"  gear: {gear if gear is not None else 'N/A'}")
    print(f"  fuel_level: {fuel if fuel is not None else 'N/A'} %")
    print(f"  fuel_rate: {extract_sensor_value(packet, 'fuel_rate') or 'N/A'} L/h")
    print(f"  engine_load: {engine_load if engine_load is not None else 'N/A'} %")
    print(f"  engine_temp: {engine_temp if engine_temp is not None else 'N/A'} C")
    print(f"  battery: {battery if battery is not None else 'N/A'} V")
    print(f"  odometer: {odometer if odometer is not None else 'N/A'} km")
    print(f"  brake_health: {brake if brake is not None else 'N/A'} %")
    print(f"  tyre_health: {tyre if tyre is not None else 'N/A'} %")


def print_analytics(analytics_result: dict) -> None:
    """Print analytics result."""
    bh = analytics_result.get("driver_behaviour", {})
    vh = analytics_result.get("vehicle_health", {})
    fe = analytics_result.get("fuel_efficiency", {})
    events = analytics_result.get("events", [])

    print("ANALYTICS")
    print(f"  driver_behaviour: {bh.get('behaviour', 'N/A')}")
    print(f"  vehicle_health: {vh.get('health', 'N/A')} (score: {vh.get('health_score', 'N/A')})")
    kml = fe.get("km_per_liter")
    mode = fe.get("mode", "N/A")
    if kml is not None:
        print(f"  fuel_efficiency: {fe.get('status', 'N/A')} ({mode}, {kml:.2f} km/L)")
    else:
        print(f"  fuel_efficiency: {fe.get('status', 'N/A')} ({mode})")
    if events:
        print(f"  events: {len(events)}")
        for e in events:
            print(f"    - {e.get('event_type', 'unknown')} ({e.get('severity', 'N/A')})")
    else:
        print("  events: none")


def main():
    """Run the continuous simulation loop."""
    tick_interval = 1.0  # seconds between ticks

    # Create runtime and vehicles
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)
    analytics = AnalyticsEngine()

    vehicles = create_vehicles(3)
    for i, v in enumerate(vehicles):
        runtime.add_vehicle(v, seed=42, index=i)

    runtime.start()

    print("=" * 70)
    print("DIGITAL TWIN CONTINUOUS SIMULATION")
    print(f"Vehicles: {len(vehicles)} | Tick interval: {tick_interval}s")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    try:
        while True:
            tick_start = time.perf_counter()

            # Advance one tick
            tick_result = runtime.step()

            # Print tick header
            time_str = tick_result.simulation_time.strftime("%H:%M:%S")
            print()
            print("=" * 70)
            print(f"TICK {tick_result.tick_id:04d} | SIMULATION TIME {time_str}")
            print("=" * 70)

            # Process each vehicle
            for vid, vtr in tick_result.vehicle_results.items():
                if vtr.error:
                    print(f"\nVEHICLE: {vid}")
                    print(f"  ERROR: {vtr.error}")
                    continue

                # Print raw telemetry from the packet
                if vtr.telemetry_packet:
                    print()
                    print_telemetry(vid, vtr.telemetry_packet)

                    # Pass the exact packet and physics result to analytics
                    analytics_result = analytics.process(
                        vtr.telemetry_packet, physics_result=vtr.physics_result,
                    )
                    print()
                    print_analytics(analytics_result)
                else:
                    print(f"\nVEHICLE: {vid}")
                    print("  No telemetry packet generated")

            # Real-time pacing
            elapsed = time.perf_counter() - tick_start
            remaining = max(0, tick_interval - elapsed)
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\n\nStopping simulation...")
    finally:
        runtime.stop()
        print("Simulation stopped.")


if __name__ == "__main__":
    main()
