"""Demonstration: Real-time driving behavior with 3 vehicles."""

import io
import contextlib
from digital_twin.common.enums import VehicleStatus
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.entities.vehicle import FuelType, TransmissionType, Vehicle, VehicleSpecification
from digital_twin.runtime.continuous_runtime import ContinuousRuntime


def main():
    config = SimulationConfig()
    runtime = ContinuousRuntime(config)

    vehicles = [
        Vehicle(
            vehicle_id="vehicle-001",
            vin="VIN000000001",
            specification=VehicleSpecification(
                manufacturer="Ford", model="Transit", year=2022,
                fuel_type=FuelType.DIESEL, transmission=TransmissionType.AUTOMATIC,
            ),
            status=VehicleStatus.AVAILABLE,
        ),
        Vehicle(
            vehicle_id="vehicle-002",
            vin="VIN000000002",
            specification=VehicleSpecification(
                manufacturer="Mercedes", model="Sprinter", year=2023,
                fuel_type=FuelType.DIESEL, transmission=TransmissionType.AUTOMATIC,
            ),
            status=VehicleStatus.AVAILABLE,
        ),
        Vehicle(
            vehicle_id="vehicle-003",
            vin="VIN000000003",
            specification=VehicleSpecification(
                manufacturer="Iveco", model="Daily", year=2021,
                fuel_type=FuelType.DIESEL, transmission=TransmissionType.MANUAL,
            ),
            status=VehicleStatus.AVAILABLE,
        ),
    ]

    for i, v in enumerate(vehicles):
        runtime.add_vehicle(v, seed=42, index=i)

    runtime.start()

    print("=" * 70)
    print("DIGITAL TWIN REAL-TIME SIMULATION (30 ticks)")
    print("=" * 70)
    print()

    for tick in range(30):
        result = runtime.step()

        vehicle_lines = []
        for vid in ["vehicle-001", "vehicle-002", "vehicle-003"]:
            v = runtime.get_vehicle(vid)
            scenario = runtime._pipelines[vid].scenario
            vehicle_lines.append(
                f"  {vid}: speed={v.state.current_speed_kmh:5.1f} km/h | "
                f"rpm={v.state.current_rpm:5.0f} | "
                f"fuel={v.state.fuel_level_percent:5.1f}% | "
                f"odometer={v.state.odometer_km:6.3f} km | "
                f"state={scenario.state.value}"
            )

        time_str = result.simulation_time.strftime("%H:%M:%S")
        print(f"TICK {result.tick_id:3d} | SIM TIME {time_str}")
        for line in vehicle_lines:
            print(line)
        print()

    runtime.stop()


if __name__ == "__main__":
    main()
