from digital_twin.simulation.simulation_runner import SimulationRunner, RunnerConfig


def main():
    config = RunnerConfig(
        fleet_size=1,
        num_ticks=1,
        real_time_pacing=False,
    )

    runner = SimulationRunner(config=config)

    print("Starting one-tick Digital Twin inspection...")
    runner.start()

    runner.run_tick()

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)

    print(runner.vehicle_state_summary("vehicle-001"))

    print(f"\nTotal packets in stream: {len(runner.stream.recent())}")


if __name__ == "__main__":
    main()