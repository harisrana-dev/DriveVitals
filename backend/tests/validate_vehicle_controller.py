"""Validation script for the Vehicle Controller layer.

Instantiates a VehicleController, builds a sample Vehicle and
DriverIntent, and runs several ticks to show throttle/brake smoothing,
gear selection, and emergency-stop override all working together.
Run directly: `python3 validate_vehicle_controller.py`
"""

from __future__ import annotations

from datetime import datetime, timedelta

from digital_twin.common.enums import SimulationStatus
from digital_twin.controller.vehicle_controller import VehicleController
from digital_twin.decision.driver_intent import DriverIntent
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
    VehicleState,
)
from digital_twin.runtime.tick_context import TickContext


def make_tick(tick_id: int, sim_time: datetime) -> TickContext:
    """Build a minimal TickContext for validation purposes."""
    return TickContext(
        tick_id=tick_id,
        simulation_time=sim_time,
        delta_time=1.0,
        clock_speed=1.0,
        random_seed=1,
        simulation_state=SimulationStatus.RUNNING,
    )


def make_intent(target_speed_kmh: float, sim_time: datetime, **overrides) -> DriverIntent:
    """Build a DriverIntent with sensible defaults for validation purposes."""
    defaults = dict(
        target_speed_kmh=target_speed_kmh,
        desired_acceleration_mps2=1.0,
        throttle_request=0.8,
        brake_request=0.0,
        steering_request=0.0,
        request_stop=False,
        request_emergency_stop=False,
        request_lane_change=False,
        overtake_requested=False,
        reason="validation",
        decision_timestamp=sim_time,
    )
    defaults.update(overrides)
    return DriverIntent(**defaults)


def main() -> None:
    vehicle = Vehicle(
        vehicle_id="veh-1",
        vin="VALIDATION0001",
        specification=VehicleSpecification(
            manufacturer="Ford",
            model="Transit",
            year=2022,
            fuel_type=FuelType.DIESEL,
            transmission=TransmissionType.AUTOMATIC,
        ),
        state=VehicleState(current_speed_kmh=0.0),
    )

    controller = VehicleController()
    sim_time = datetime(2026, 7, 17, 9, 0, 0)
    previous_actuation = None
    ticks_since_last_shift = 999  # allow an immediate first shift

    print("--- Accelerating from a stop toward 80 km/h ---")
    for tick_id in range(1, 6):
        sim_time += timedelta(seconds=1)
        tick_context = make_tick(tick_id, sim_time)
        intent = make_intent(target_speed_kmh=80.0, sim_time=sim_time)

        actuation = controller.compute_actuation(
            intent=intent,
            vehicle=vehicle,
            tick_context=tick_context,
            previous_actuation=previous_actuation,
            ticks_since_last_shift=ticks_since_last_shift,
        )

        if previous_actuation is None or (
            actuation.requested_gear != previous_actuation.requested_gear
        ):
            ticks_since_last_shift = 0
        else:
            ticks_since_last_shift += 1

        print(
            f"tick={tick_id} throttle={actuation.throttle_percentage:.3f} "
            f"brake={actuation.brake_percentage:.3f} "
            f"gear={actuation.requested_gear.position.value}"
            f"{actuation.requested_gear.gear_number or ''} "
            f"clutch={actuation.clutch_engaged} reason='{actuation.controller_reason}'"
        )

        previous_actuation = actuation
        vehicle.state.current_speed_kmh = min(80.0, vehicle.state.current_speed_kmh + 10.0)

    print()
    print("--- Emergency stop overrides everything ---")
    sim_time += timedelta(seconds=1)
    tick_context = make_tick(6, sim_time)
    emergency_intent = make_intent(
        target_speed_kmh=0.0,
        sim_time=sim_time,
        throttle_request=0.0,
        brake_request=1.0,
        request_emergency_stop=True,
        reason="hazard ahead",
    )
    emergency_actuation = controller.compute_actuation(
        intent=emergency_intent,
        vehicle=vehicle,
        tick_context=tick_context,
        previous_actuation=previous_actuation,
        ticks_since_last_shift=ticks_since_last_shift,
    )
    print(emergency_actuation)

    assert emergency_actuation.brake_percentage == 1.0
    assert emergency_actuation.throttle_percentage == 0.0

    print()
    print("VEHICLE CONTROLLER VALIDATION PASSED")


if __name__ == "__main__":
    main()