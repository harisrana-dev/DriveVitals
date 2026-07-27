#!/usr/bin/env python
"""
DriveVitals Fleet Analytics Demo.

Runs multiple configured vehicles and drivers through the fleet runtime,
publishes every TelemetrySample through the telemetry pipeline, and prints
raw telemetry together with contextual, driver-behaviour, and temporal event
analytics.

Usage:
    python -m scripts.run_fleet_telemetry
"""

from datetime import datetime, timedelta
import time

from backend.fleet.config.fleet_factory import FleetFactory
from backend.fleet.runtime.fleet_runner import FleetRunner
from backend.telemetry.models.telemetry_sample import TelemetrySample
from backend.fleet.models.trip import Trip

from backend.pipeline.telemetry_pipeline import TelemetryPipeline

from backend.analytics.engine import AnalyticsEngine
from backend.analytics.state.runtime_state_store import RuntimeStateStore
from backend.analytics.context.context_store import AnalyticsContextStore
from backend.analytics.context.analytics_context import AnalyticsContext

from backend.analytics.behaviour.detection.analyzer import (
    DriverBehaviourAnalyzer,
)

from backend.analytics.behaviour.events.tracker import (
    BehaviourEventTracker,
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


def print_sample(
    sample: TelemetrySample,
    analysis_input,
    behaviour_analysis,
    completed_events,
    tick: int,
) -> None:
    """Print one complete telemetry + analytics record."""

    context = analysis_input.context

    print()
    print(
        "╔══════════════════════════════════════════════════════════════════════════════╗"
    )

    print(
        f"║ TICK {tick:<5} "
        f"│ {sample.timestamp} "
        f"│ {sample.vehicle_id:<8} "
        f"│ DRIVER {sample.driver_id:<6}"
    )

    print(
        "╠══════════════════════════════════════════════════════════════════════════════╣"
    )

    # ------------------------------------------------------------------
    # Identity / context
    # ------------------------------------------------------------------

    print(
        f"║ TRIP: {sample.trip_id:<12} "
        f"ROUTE: {context.route_id:<8} "
        f"TYPE: {context.route_type:<10}"
    )

    print(
        f"║ VEHICLE: {context.vehicle_make} "
        f"{context.vehicle_model} "
        f"({context.vehicle_year})"
    )

    print(
        f"║ SPEED LIMIT: {context.speed_limit_kmh:>6.1f} km/h"
    )

    print(
        "╠──────────────────────────────────────────────────────────────────────────────╣"
    )

    # ------------------------------------------------------------------
    # Raw telemetry
    # ------------------------------------------------------------------

    print(
        f"║ SPEED       {sample.speed_kmh:>8.2f} km/h"
        f"    RPM          {sample.rpm:>8.0f}"
        f"    ENGINE LOAD  {sample.engine_load_percent:>8.1f} %"
    )

    print(
        f"║ THROTTLE    {sample.throttle_position_percent:>8.1f} %"
        f"    BRAKE        {sample.brake_pressure:>8.2f}"
    )

    print(
        f"║ COOLANT     {sample.coolant_temperature_c:>8.1f} °C"
        f"    FUEL RATE    {sample.fuel_rate_lph:>8.2f} L/h"
    )

    print(
        f"║ FUEL LEVEL   {sample.fuel_level_percent:>7.2f} %"
        f"    ODOMETER    {sample.odometer_km:>9.2f} km"
    )

    print(
        "╠──────────────────────────────────────────────────────────────────────────────╣"
    )

    # ------------------------------------------------------------------
    # Current driver behaviour
    # ------------------------------------------------------------------

    print(
        f"║ BEHAVIOUR   "
        f"Speeding: "
        f"{'YES' if behaviour_analysis.speeding else 'NO':<3}"
        f"  (+{behaviour_analysis.speed_excess_kmh:>5.1f} km/h)"
    )

    print(
        f"║             "
        f"Harsh Braking: "
        f"{'YES' if behaviour_analysis.harsh_braking else 'NO':<3}"
        f"  | Aggressive Throttle: "
        f"{'YES' if behaviour_analysis.aggressive_throttle else 'NO':<3}"
    )

    print(
        f"║             "
        f"High RPM: "
        f"{'YES' if behaviour_analysis.high_rpm else 'NO':<3}"
        f"  | SEVERITY: "
        f"{behaviour_analysis.severity.upper()}"
    )

    # ------------------------------------------------------------------
    # Completed temporal behaviour events
    # ------------------------------------------------------------------

    if completed_events:

        print(
            "╠──────────────────────────────────────────────────────────────────────────────╣"
        )

        print("║ COMPLETED EVENTS:")

        for event in completed_events:

            print(
                f"║   {event.event_type.upper():<22}"
                f" Duration: {event.duration_seconds:>6.1f}s"
                f" | Severity: {event.severity.upper()}"
            )

            print(
                f"║   Started: {event.started_at}"
            )

            print(
                f"║   Ended:   {event.ended_at}"
            )

            print(
                f"║   Max Speed Excess: "
                f"{event.max_speed_excess_kmh:>5.1f} km/h"
            )

    print(
        "╚══════════════════════════════════════════════════════════════════════════════╝"
    )


def main() -> None:

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

    configured_fleet = FleetFactory.from_config()

    fleet = FleetRunner(
        tick_seconds=tick_seconds,
    )

    # ------------------------------------------------------------------
    # Analytics pipeline
    # ------------------------------------------------------------------

    pipeline = TelemetryPipeline()

    runtime_store = RuntimeStateStore()
    context_store = AnalyticsContextStore()

    driver_behaviour_analyzer = DriverBehaviourAnalyzer()
    event_tracker = BehaviourEventTracker()
    behaviour_summarizer = DriverBehaviourSummarizer()

    analytics_engine = AnalyticsEngine(
        runtime_store=runtime_store,
        context_store=context_store,
        driver_behaviour_analyzer=driver_behaviour_analyzer,
        event_tracker=event_tracker,
        behaviour_summarizer=behaviour_summarizer,
    )

    pipeline.register(
        analytics_engine
    )

    # ------------------------------------------------------------------
    # Register fleet assignments and analytics context
    # ------------------------------------------------------------------

    for assignment in configured_fleet.assignments:

        vehicle = next(
            v
            for v in configured_fleet.vehicles
            if v.vehicle_id == assignment.vehicle_id
        )

        driver = next(
            d
            for d in configured_fleet.drivers
            if d.driver_id == assignment.driver_id
        )

        route = next(
            r
            for r in configured_fleet.routes
            if r.route_id == assignment.route_id
        )

        trip = Trip(
            trip_id=f"T-{assignment.assignment_id}",
            vehicle_id=vehicle.vehicle_id,
            driver_id=driver.driver_id,
            route_id=route.route_id,
        )

        context_store.register(
            AnalyticsContext(
                vehicle_id=vehicle.vehicle_id,
                driver_id=driver.driver_id,
                trip_id=trip.trip_id,
                route_id=route.route_id,
                route_type=route.route_type,
                speed_limit_kmh=route.speed_limit_kmh,
                vehicle_make=vehicle.make,
                vehicle_model=vehicle.model,
                vehicle_year=vehicle.year,
            )
        )

        fleet.add_assignment(
            assignment=assignment,
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
        )

    # ------------------------------------------------------------------
    # Start simulation
    # ------------------------------------------------------------------

    print("\033[2J\033[H", end="")

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

    now = start_time

    tick = 0

    fleet.start_all(
        now=now
    )

    # ------------------------------------------------------------------
    # Main simulation loop
    # ------------------------------------------------------------------

    while fleet.active_runners():

        samples = fleet.tick_all(
            now=now
        )

        for sample in samples:

            # ----------------------------------------------------------
            # 1. Publish telemetry
            # ----------------------------------------------------------

            pipeline.publish(sample)

            analysis_input = analytics_engine.get_input(
                sample.vehicle_id
            )

            behaviour_analysis = analytics_engine.get_behaviour_analysis(
                sample.vehicle_id
            )

            completed_events = analytics_engine.drain_completed_events(
                vehicle_id=sample.vehicle_id,
            )

            if analysis_input is None or behaviour_analysis is None:
                continue
            # ----------------------------------------------------------
            # 5. Print complete result
            # ----------------------------------------------------------

            print_sample(
                sample=sample,
                analysis_input=analysis_input,
                behaviour_analysis=behaviour_analysis,
                completed_events=completed_events,
                tick=tick,
            )

        tick += 1

        now += timedelta(
            seconds=tick_seconds
        )

        time.sleep(
            tick_seconds
        )

    # ------------------------------------------------------------------
    # Flush any events still active when simulation ends
    # ------------------------------------------------------------------

    final_events = event_tracker.flush(
        timestamp=now
    )

    if final_events:

        print()

        print(
            "══════════════════════════════════════════════════════════════════════════════"
        )

        print(
            "                     FINAL ACTIVE EVENTS FLUSHED"
        )

        print(
            "══════════════════════════════════════════════════════════════════════════════"
        )

        for event in final_events:

            print(
                f"{event.event_type.upper():<24}"
                f" Duration: {event.duration_seconds:>6.1f}s"
                f" | Severity: {event.severity.upper()}"
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