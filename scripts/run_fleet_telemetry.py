#!/usr/bin/env python

"""
DriveVitals Fleet Analytics Demo.

Runs multiple configured vehicles and drivers through the fleet runtime,
publishes every TelemetrySample through the telemetry pipeline, and prints
the latest AnalyticsSnapshot produced by the analytics engine.

Runtime flow:

    FleetRunner
        ↓
    TelemetrySample
        ↓
    TelemetryPipeline
        ↓
    AnalyticsEngine
        ↓
    AnalyticsSnapshot
        ├── Telemetry
        ├── Driver Behaviour Analysis
        ├── Completed Behaviour Events
        └── Active Behaviour Events

Usage:

    python -m scripts.run_fleet_telemetry
"""


from datetime import datetime, timedelta
import time


from backend.fleet.config.fleet_factory import (
    FleetFactory,
)

from backend.fleet.models.trip import (
    Trip,
)

from backend.fleet.runtime.fleet_runner import (
    FleetRunner,
)


from backend.pipeline.telemetry_pipeline import (
    TelemetryPipeline,
)


from backend.analytics.engine import (
    AnalyticsEngine,
)

from backend.analytics.state.runtime_state_store import (
    RuntimeStateStore,
)

from backend.analytics.context.context_store import (
    AnalyticsContextStore,
)

from backend.analytics.context.analytics_context import (
    AnalyticsContext,
)

from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)

from backend.analytics.behaviour.events.tracker import (
    BehaviourEventTracker,
)

from backend.analytics.behaviour.aggregation.summarizer import (
    DriverBehaviourSummarizer,
)

from backend.analytics.snapshot.snapshot_store import (
    AnalyticsSnapshotStore,
)


def print_snapshot(
    snapshot,
    tick: int,
) -> None:

    """
    Print one complete analytics snapshot.

    The snapshot is the single source of truth for the current
    point-in-time telemetry and behaviour state.
    """

    telemetry = (
        snapshot.telemetry
    )

    behaviour = (
        snapshot.behaviour
    )


    print()


    print(
        "╔══════════════════════════════════════════════════════════════════════════════╗"
    )


    print(
        f"║ TICK {tick:<5} "
        f"│ {snapshot.timestamp} "
        f"│ {snapshot.vehicle_id:<8} "
        f"│ DRIVER {snapshot.driver_id:<6}"
    )


    print(
        "╠══════════════════════════════════════════════════════════════════════════════╣"
    )


    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    print(
        f"║ TRIP: {snapshot.trip_id:<12}"
    )


    print(
        "╠──────────────────────────────────────────────────────────────────────────────╣"
    )


    # ------------------------------------------------------------------
    # Raw telemetry
    # ------------------------------------------------------------------

    print(
        "║ TELEMETRY"
    )


    print(
        f"║ SPEED        "
        f"{telemetry.speed_kmh:>8.2f} km/h"
        f"    RPM          "
        f"{telemetry.rpm:>8.0f}"
    )


    print(
        f"║ ENGINE LOAD  "
        f"{telemetry.engine_load_percent:>8.1f} %"
        f"    THROTTLE     "
        f"{telemetry.throttle_position_percent:>8.1f} %"
    )


    print(
        f"║ BRAKE        "
        f"{telemetry.brake_pressure:>8.2f}"
        f"    COOLANT      "
        f"{telemetry.coolant_temperature_c:>8.1f} °C"
    )


    print(
        f"║ FUEL RATE    "
        f"{telemetry.fuel_rate_lph:>8.2f} L/h"
        f"    FUEL LEVEL   "
        f"{telemetry.fuel_level_percent:>8.2f} %"
    )


    print(
        f"║ ODOMETER     "
        f"{telemetry.odometer_km:>8.2f} km"
    )


    print(
        "╠──────────────────────────────────────────────────────────────────────────────╣"
    )


    # ------------------------------------------------------------------
    # Current driver behaviour
    # ------------------------------------------------------------------

    print(
        "║ DRIVER BEHAVIOUR"
    )


    print(
        f"║ SPEEDING            "
        f"{'YES' if behaviour.speeding else 'NO':<3}"
        f"   Excess: "
        f"{behaviour.speed_excess_kmh:>6.1f} km/h"
    )


    print(
        f"║ HARSH BRAKING       "
        f"{'YES' if behaviour.harsh_braking else 'NO':<3}"
    )


    print(
        f"║ AGGRESSIVE THROTTLE "
        f"{'YES' if behaviour.aggressive_throttle else 'NO':<3}"
    )


    print(
        f"║ HIGH RPM             "
        f"{'YES' if behaviour.high_rpm else 'NO':<3}"
    )


    print(
        f"║ SEVERITY             "
        f"{behaviour.severity.upper()}"
    )


    # ------------------------------------------------------------------
    # Temporal event state
    # ------------------------------------------------------------------

    print(
        "╠──────────────────────────────────────────────────────────────────────────────╣"
    )


    print(
        "║ TEMPORAL EVENTS"
    )


    if snapshot.active_event_types:

        print(
            f"║ ACTIVE: "
            f"{', '.join(snapshot.active_event_types).upper()}"
        )

    else:

        print(
            "║ ACTIVE: NONE"
        )


    if snapshot.completed_events:

        print(
            "║"
        )


        print(
            "║ COMPLETED EVENTS:"
        )


        for event in snapshot.completed_events:

            print(
                f"║   {event.event_type.upper():<22}"
                f" Duration: "
                f"{event.duration_seconds:>6.1f}s"
                f" | Distance: "
                f"{event.distance_km:>6.2f} km"
                f" | Severity: "
                f"{event.severity.upper()}"
            )


            print(
                f"║   Started: "
                f"{event.started_at}"
            )


            print(
                f"║   Ended:   "
                f"{event.ended_at}"
            )


            print(
                f"║   Max Speed Excess: "
                f"{event.max_speed_excess_kmh:>5.1f} km/h"
            )

    else:

        print(
            "║ COMPLETED: NONE"
        )


    print(
        "╚══════════════════════════════════════════════════════════════════════════════╝"
    )


def main() -> None:

    # ------------------------------------------------------------------
    # Simulation configuration
    # ------------------------------------------------------------------

    start_time = datetime(
        2025,
        1,
        15,
        8,
        0,
        0,
    )


    tick_seconds = 1.0


    # ------------------------------------------------------------------
    # Load configured fleet
    # ------------------------------------------------------------------

    configured_fleet = (
        FleetFactory.from_config()
    )


    fleet = FleetRunner(
        tick_seconds=tick_seconds,
    )


    # ------------------------------------------------------------------
    # Create telemetry pipeline
    # ------------------------------------------------------------------

    pipeline = (
        TelemetryPipeline()
    )


    # ------------------------------------------------------------------
    # Create analytics components
    # ------------------------------------------------------------------

    runtime_store = (
        RuntimeStateStore()
    )


    context_store = (
        AnalyticsContextStore()
    )


    driver_behaviour_analyzer = (
        DriverBehaviourAnalyzer()
    )


    event_tracker = (
        BehaviourEventTracker()
    )


    behaviour_summarizer = (
        DriverBehaviourSummarizer()
    )


    snapshot_store = (
        AnalyticsSnapshotStore()
    )


    analytics_engine = AnalyticsEngine(

        runtime_store=runtime_store,

        context_store=context_store,

        driver_behaviour_analyzer=(
            driver_behaviour_analyzer
        ),

        event_tracker=event_tracker,

        behaviour_summarizer=(
            behaviour_summarizer
        ),

        snapshot_store=snapshot_store,

    )


    # ------------------------------------------------------------------
    # Register analytics as a telemetry consumer
    # ------------------------------------------------------------------

    pipeline.register(
        analytics_engine
    )


    # ------------------------------------------------------------------
    # Register fleet assignments and analytics context
    # ------------------------------------------------------------------

    for assignment in (
        configured_fleet.assignments
    ):

        vehicle = next(

            vehicle

            for vehicle
            in configured_fleet.vehicles

            if (
                vehicle.vehicle_id
                == assignment.vehicle_id
            )

        )


        driver = next(

            driver

            for driver
            in configured_fleet.drivers

            if (
                driver.driver_id
                == assignment.driver_id
            )

        )


        route = next(

            route

            for route
            in configured_fleet.routes

            if (
                route.route_id
                == assignment.route_id
            )

        )


        trip = Trip(

            trip_id=(
                f"T-{assignment.assignment_id}"
            ),

            vehicle_id=(
                vehicle.vehicle_id
            ),

            driver_id=(
                driver.driver_id
            ),

            route_id=(
                route.route_id
            ),

        )


        # --------------------------------------------------------------
        # Register immutable analytics context.
        # --------------------------------------------------------------

        context_store.register(

            AnalyticsContext(

                vehicle_id=(
                    vehicle.vehicle_id
                ),

                driver_id=(
                    driver.driver_id
                ),

                trip_id=(
                    trip.trip_id
                ),

                route_id=(
                    route.route_id
                ),

                route_type=(
                    route.route_type
                ),

                speed_limit_kmh=(
                    route.speed_limit_kmh
                ),

                vehicle_make=(
                    vehicle.make
                ),

                vehicle_model=(
                    vehicle.model
                ),

                vehicle_year=(
                    vehicle.year
                ),

            )

        )


        # --------------------------------------------------------------
        # Register runtime vehicle.
        # --------------------------------------------------------------

        fleet.add_assignment(

            assignment=assignment,

            vehicle=vehicle,

            driver=driver,

            route=route,

            trip=trip,

        )


    # ------------------------------------------------------------------
    # Start output
    # ------------------------------------------------------------------

    print(
        "\033[2J\033[H",
        end="",
    )


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


    print(
        "                    DriveVitals Fleet Analytics Stream"
    )


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


    print()


    # ------------------------------------------------------------------
    # Start fleet
    # ------------------------------------------------------------------

    now = (
        start_time
    )


    tick = 0


    fleet.start_all(
        now=now,
    )


    # ------------------------------------------------------------------
    # Main simulation loop
    # ------------------------------------------------------------------

    while fleet.active_runners():

        # --------------------------------------------------------------
        # 1. FleetRunner advances all active vehicles.
        #
        # This produces raw TelemetrySample objects.
        # --------------------------------------------------------------

        samples = (
            fleet.tick_all(
                now=now,
            )
        )


        for sample in samples:

            # ----------------------------------------------------------
            # 2. TelemetryPipeline distributes the raw sample.
            #
            # AnalyticsEngine receives it automatically because it was
            # registered as a pipeline consumer.
            # ----------------------------------------------------------

            pipeline.publish(
                sample
            )


            # ----------------------------------------------------------
            # 3. Retrieve latest AnalyticsSnapshot.
            # ----------------------------------------------------------

            snapshot = (
                analytics_engine.get_snapshot(
                    sample.vehicle_id
                )
            )


            if snapshot is None:

                continue


            # ----------------------------------------------------------
            # 4. Print latest snapshot.
            # ----------------------------------------------------------

            print_snapshot(

                snapshot=snapshot,

                tick=tick,

            )


        # --------------------------------------------------------------
        # Advance simulation clock.
        # --------------------------------------------------------------

        tick += 1


        now += timedelta(
            seconds=tick_seconds
        )


        time.sleep(
            tick_seconds
        )


    # ------------------------------------------------------------------
    # Flush remaining active events for each vehicle.
    # ------------------------------------------------------------------

    print()


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


    print(
        "                     FINAL EVENTS FLUSH"
    )


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


    for runner in (
        fleet.all_runners()
    ):

        vehicle_id = (
            runner.vehicle.vehicle_id
        )


        final_events = (
            analytics_engine.flush_vehicle(

                vehicle_id=vehicle_id,

                timestamp=now,

            )
        )


        for event in final_events:

            print(

                f"{vehicle_id:<10}"

                f"{event.event_type.upper():<24}"

                f"Duration: "
                f"{event.duration_seconds:>6.1f}s"

                f" | Distance: "
                f"{event.distance_km:>6.2f} km"

                f" | Severity: "
                f"{event.severity.upper()}"

            )


    print()


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


    print(
        "                         ALL TRIPS COMPLETED"
    )


    print(
        "══════════════════════════════════════════════════════════════════════════════"
    )


if __name__ == "__main__":

    main()