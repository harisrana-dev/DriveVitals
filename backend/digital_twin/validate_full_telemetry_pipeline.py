"""End-to-end validation of the Digital Twin telemetry pipeline.

Validates the complete flow:

    VehicleState
        ↓
    VirtualSensorProvider
        ↓
    SensorReadings
        ↓
    TelemetryGenerator
        ↓
    TelemetryPacket
        ↓
    TelemetryPipeline
        ↓
    InMemoryTelemetryStream

This validates the telemetry boundary of the Digital Twin without
introducing database, API, WebSocket, or networking dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
    VehicleState,
)
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors.virtual_sensor_provider import VirtualSensorProvider
from digital_twin.telemetry.telemetry_generator import TelemetryGenerator
from digital_twin.telemetry.telemetry_pipeline import TelemetryPipeline
from digital_twin.telemetry.telemetry_stream import InMemoryTelemetryStream
from digital_twin.common.enums import SimulationStatus


def create_vehicle() -> Vehicle:
    """Create a deterministic validation vehicle."""

    return Vehicle(
        vehicle_id="validation-vehicle-001",
        vin="VALIDATIONVIN001",
        specification=VehicleSpecification(
            manufacturer="Ford",
            model="Transit",
            year=2022,
            fuel_type=FuelType.DIESEL,
            transmission=TransmissionType.AUTOMATIC,
        ),
        state=VehicleState(
            current_speed_kmh=60.0,
            current_rpm=2200.0,
            current_gear=4,
            fuel_level_percent=72.5,
            engine_load_percent=48.0,
            engine_temperature_celsius=88.0,
            battery_voltage=13.9,
            brake_wear_percent=12.0,
            tyre_wear_percent=8.0,
            odometer_km=12540.5,
        ),
    )


def create_tick(
    tick_id: int,
    simulation_time: datetime,
) -> TickContext:
    return TickContext(
        tick_id=tick_id,
        simulation_time=simulation_time,
        delta_time=1.0,
        clock_speed=1.0,
        random_seed=42,
        simulation_state=SimulationStatus.RUNNING,
    )


def main() -> None:
    """Run the complete telemetry pipeline validation."""

    print("=" * 70)
    print("DRIVEVITALS DIGITAL TWIN")
    print("END-TO-END TELEMETRY PIPELINE VALIDATION")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Create the Digital Twin vehicle
    # ------------------------------------------------------------------

    vehicle = create_vehicle()

    print("\n[1/7] Vehicle created")
    print(f"      Vehicle ID: {vehicle.vehicle_id}")
    print(f"      Speed:      {vehicle.state.current_speed_kmh} km/h")
    print(f"      RPM:        {vehicle.state.current_rpm}")

    original_state = vehicle.state

    # ------------------------------------------------------------------
    # 2. Create Virtual Sensor Provider
    # ------------------------------------------------------------------

    sensor_provider = VirtualSensorProvider()

    print("\n[2/7] Virtual sensor provider created")

    # ------------------------------------------------------------------
    # 3. Create Telemetry Generator
    # ------------------------------------------------------------------

    generator = TelemetryGenerator()

    print("[3/7] Telemetry generator created")

    # ------------------------------------------------------------------
    # 4. Create telemetry stream and pipeline
    # ------------------------------------------------------------------

    stream = InMemoryTelemetryStream()
    pipeline = TelemetryPipeline(stream=stream)

    print("[4/7] Telemetry pipeline created")

    # ------------------------------------------------------------------
    # 5. Generate telemetry across multiple simulation ticks
    # ------------------------------------------------------------------

    simulation_time = datetime(2026, 7, 20, 10, 0, 0)

    generated_packets = []

    print("\n[5/7] Running telemetry generation")

    for tick_id in range(1, 6):

        simulation_time += timedelta(seconds=1)

        tick_context = create_tick(
            tick_id=tick_id,
            simulation_time=simulation_time,
        )

        # Sensors observe the current VehicleState.
        sensor_readings = sensor_provider.update_all(
            vehicle=vehicle,
            tick_context=tick_context,
        )

        # Generate one immutable packet for this tick.
        packet = generator.generate(
            vehicle=vehicle,
            sensor_readings=sensor_readings,
            tick_context=tick_context,
        )

        # Process and publish the packet.
        processed_packet = pipeline.process(packet)

        generated_packets.append(processed_packet)

        print(
            f"      Tick {tick_id}: "
            f"{len(sensor_readings)} sensor readings → "
            f"sequence {processed_packet.sequence_number}"
        )

        # Simulate a small state change between ticks.
        # This represents the Digital Twin evolving between observations.
        vehicle.state.current_speed_kmh += 2.0
        vehicle.state.current_rpm += 100.0

    # ------------------------------------------------------------------
    # 6. Validate packet sequencing and stream delivery
    # ------------------------------------------------------------------

    print("\n[6/7] Validating telemetry stream")

    recent_packets = stream.recent()

    assert len(recent_packets) == 5
    assert len(generated_packets) == 5

    # Sequence numbers must be monotonically increasing.
    sequence_numbers = [
        packet.sequence_number
        for packet in recent_packets
    ]

    assert sequence_numbers == [0, 1, 2, 3, 4]

    # Tick IDs must be preserved.
    tick_ids = [
        packet.tick_id
        for packet in recent_packets
    ]

    assert tick_ids == [1, 2, 3, 4, 5]

    # Vehicle identity must be preserved.
    assert all(
        packet.vehicle_id == vehicle.vehicle_id
        for packet in recent_packets
    )

    print(f"      Packets published: {len(recent_packets)}")
    print(f"      Sequence numbers:   {sequence_numbers}")
    print(f"      Tick IDs:           {tick_ids}")

    # ------------------------------------------------------------------
    # 7. Validate sensor data and immutability boundary
    # ------------------------------------------------------------------

    print("\n[7/7] Validating telemetry contents")

    first_packet = recent_packets[0]

    assert first_packet.sensor_readings
    assert len(first_packet.sensor_readings) > 0

    print(
        f"      Sensor readings in first packet: "
        f"{len(first_packet.sensor_readings)}"
    )

    for reading in first_packet.sensor_readings:
        assert reading.sensor_name
        assert reading.timestamp is not None
        assert reading.unit
        assert reading.valid is True

    # The VehicleState object should remain valid and accessible.
    assert vehicle.state is not None

    print("      All sensor readings valid")

    # ------------------------------------------------------------------
    # Validate FIFO consumption
    # ------------------------------------------------------------------

    consumed_packets = []

    while True:
        packet = stream.consume()

        if packet is None:
            break

        consumed_packets.append(packet)

    assert len(consumed_packets) == 5
    assert stream.consume() is None

    # recent() must remain non-destructive after consume().
    assert len(stream.recent()) == 5

    print("      FIFO consumption validated")
    print("      Historical packet retention validated")

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("END-TO-END TELEMETRY PIPELINE VALIDATION PASSED")
    print("=" * 70)

    print("\nValidated:")
    print("  ✓ VehicleState → VirtualSensorProvider")
    print("  ✓ Virtual sensors → SensorReadings")
    print("  ✓ SensorReadings → TelemetryGenerator")
    print("  ✓ TelemetryGenerator → TelemetryPacket")
    print("  ✓ TelemetryPacket → TelemetryPipeline")
    print("  ✓ TelemetryPipeline → InMemoryTelemetryStream")
    print("  ✓ Sequence numbers")
    print("  ✓ Tick IDs")
    print("  ✓ Vehicle identity")
    print("  ✓ Sensor readings")
    print("  ✓ FIFO consumption")
    print("  ✓ Historical packet retention")


if __name__ == "__main__":
    main()