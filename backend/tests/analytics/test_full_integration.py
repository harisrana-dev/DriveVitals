"""Full integration: Digital Twin -> AnalyticsEngine -> structured output.

Runs the simulation, captures real TelemetryPackets + PhysicsTickResults +
Trip data, feeds them through the new AnalyticsEngine, and prints
representative output for all three gaps.
"""

from digital_twin.simulation.simulation_runner import RunnerConfig, SimulationRunner
from analytics.engine import AnalyticsEngine


def main():
    config = RunnerConfig(
        fleet_size=10,
        num_ticks=10000,
        real_time_pacing=False,
    )

    # Suppress simulation print output for cleaner integration test
    import io, contextlib
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        runner = SimulationRunner(config=config)
        runner.start()

        analytics = AnalyticsEngine()

        for tick in range(config.num_ticks):
            runner.run_tick()

            # Feed each vehicle's latest packet + physics + trip through analytics
            for vehicle_id in runner.vehicle_ids:
                unit = runner._vehicle_units[vehicle_id]
                if unit.last_packet is not None:
                    result = analytics.process(
                        unit.last_packet,
                        physics_result=unit.last_physics_result,
                        trip=unit.trip_entity,
                    )

    # Print representative analytics output for one vehicle
    print("=" * 70)
    print("ANALYTICS INTEGRATION TEST — REPRESENTATIVE OUTPUT")
    print("=" * 70)

    # Run one more tick to get fresh output
    f2 = io.StringIO()
    with contextlib.redirect_stdout(f2):
        runner.run_tick()

    for vehicle_id in runner.vehicle_ids:
        unit = runner._vehicle_units[vehicle_id]
        if unit.last_packet is not None:
            result = analytics.process(
                unit.last_packet,
                physics_result=unit.last_physics_result,
                trip=unit.trip_entity,
            )

            print(f"\n{'='*70}")
            print(f"VEHICLE: {vehicle_id}")
            print(f"{'='*70}")
            print(f"  Tick:          {result['tick_id']}")
            print(f"  Timestamp:     {result['timestamp']}")

            # Events (lifecycle-tracked)
            events = result["events"]
            print(f"  Events:        {len(events)} active")
            for e in events:
                print(f"    - [{e['severity']}] {e['event_type']} "
                      f"(occurrences={e['occurrences']}, "
                      f"latest={e['latest_value']:.2f})")

            print(f"  Driver:        {result['driver_behaviour']['behaviour']}")
            print(f"  Health:        {result['vehicle_health']['health']} "
                  f"(score: {result['vehicle_health']['health_score']})")
            if result['vehicle_health']['factors']:
                for factor in result['vehicle_health']['factors']:
                    print(f"    - {factor}")

            # Fuel efficiency (from real physics)
            fe = result["fuel_efficiency"]
            print(f"  Fuel:          {fe['status']} ({fe.get('mode', 'n/a')})")
            if fe.get("km_per_liter") is not None:
                print(f"    km/L:        {fe['km_per_liter']} ({fe['rating']})")
                print(f"    distance:    {fe['distance_travelled_km']} km")
                print(f"    consumed:    {fe['fuel_consumed_liters']} L")

            # Trip performance (from real trip domain)
            tp = result["trip_performance"]
            print(f"  Trip:          {tp['status']}")
            if tp["status"] == "in_progress":
                print(f"    trip_id:     {tp['trip_id']}")
                print(f"    progress:    {tp['progress_percent']}%")
                print(f"    remaining:   {tp['distance_remaining_km']} km")
                print(f"    avg speed:   {tp['average_speed_kmh']} km/h")
                print(f"    fuel eff:    {tp['fuel_efficiency_km_per_liter']} km/L")

            print(f"  Ranking:       {result['driver_ranking']['score']}/100 "
                  f"({result['driver_ranking']['grade']})")
            print(f"  Maintenance:   {len(result['maintenance_queue'])} items")
            for m in result["maintenance_queue"]:
                print(f"    - [{m['priority']}] {m['maintenance']}")

    print(f"\n{'='*70}")
    print("FLEET TRENDS (last snapshot):")
    if result["fleet_trends"]:
        latest = result["fleet_trends"][-1]
        for k, v in latest.items():
            if k != "timestamp":
                print(f"  {k}: {v}")

    # Event lifecycle summary
    active = analytics.event_manager.get_active_events()
    resolved = analytics.event_manager.get_resolved_events()
    print(f"\n{'='*70}")
    print(f"EVENT LIFECYCLE: {len(active)} active, {len(resolved)} resolved")
    for e in resolved[:5]:
        print(f"  - RESOLVED: {e.event_type} ({e.vehicle_id}) "
              f"occurrences={e.occurrences}")

    print(f"{'='*70}")
    print("\nINTEGRATION TEST PASSED")


if __name__ == "__main__":
    main()
