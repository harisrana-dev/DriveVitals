from digital_twin.simulation.simulation_runner import (
    RunnerConfig,
    SimulationRunner,
)


def main() -> None:
    runner = SimulationRunner(
        RunnerConfig(
            fleet_size=1,
            num_ticks=10,
            real_time_pacing=False,
        )
    )

    runner.start()

    vehicle_id = runner.vehicle_ids[0]

    print("\n" + "=" * 90)
    print("10-TICK DIGITAL TWIN STATE EVOLUTION")
    print("=" * 90)

    print(
        f"{'TICK':<6}"
        f"{'SIM TIME':<12}"
        f"{'SPEED':>12}"
        f"{'RPM':>10}"
        f"{'GEAR':>8}"
        f"{'ODOMETER':>14}"
        f"{'FUEL':>12}"
    )

    print("-" * 90)

    for _ in range(10):
        tick_context = runner.run_tick()

        unit = runner._vehicle_units[vehicle_id]
        state = unit.vehicle_entity.state

        print(
            f"{tick_context.tick_id:<6}"
            f"{tick_context.simulation_time.strftime('%H:%M:%S'):<12}"
            f"{state.current_speed_kmh:>12.3f}"
            f"{state.current_rpm:>10.1f}"
            f"{state.current_gear:>8}"
            f"{state.odometer_km:>14.6f}"
            f"{state.fuel_level_percent:>12.6f}"
        )

    print("-" * 90)
    print(f"Packets in stream: {len(runner.stream.recent())}")
    print("=" * 90)


if __name__ == "__main__":
    main()