from simulation.runner import RunnerConfig, SimulationRunner


def main():
    runner = SimulationRunner(
        RunnerConfig(
            fleet_size=3,
            real_time=True,
        )
    )

    for i in range(1, 4):
        runner.create_and_register_vehicle(
            f"vehicle-{i:03d}"
        )

    runner.start()
    runner.run()


if __name__ == "__main__":
    main()