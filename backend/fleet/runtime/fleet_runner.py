"""
Fleet Runner.

Coordinates multiple VehicleRunner instances so several
vehicle/driver/route assignments can operate independently.

The FleetRunner is responsible only for fleet execution.

It:
    - owns active VehicleRunner instances
    - starts trips
    - advances active vehicles tick by tick
    - receives generated TelemetrySample objects
    - forwards telemetry to a caller-provided sink

It does not:
    - perform analytics
    - write to a database
    - publish WebSocket messages
    - interpret driver behavior

This keeps the fleet runtime independent from downstream consumers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional

from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver
from backend.fleet.models.route import Route
from backend.fleet.models.trip import Trip
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.vehicle_runner import VehicleRunner
from backend.telemetry.models.telemetry_sample import TelemetrySample


TelemetrySink = Callable[[TelemetrySample], None]


@dataclass
class FleetRunner:
    tick_seconds: float = 1.0
    _runners: List[VehicleRunner] = field(default_factory=list)

    def add_assignment(
        self,
        assignment: Assignment,
        vehicle: Vehicle,
        driver: Driver,
        route: Route,
        trip: Trip,
    ) -> VehicleRunner:
        """
        Register a new vehicle run for an assignment.
        """

        runner = VehicleRunner(
            vehicle=vehicle,
            driver=driver,
            route=route,
            trip=trip,
            tick_seconds=self.tick_seconds,
        )

        self._runners.append(runner)

        return runner

    def active_runners(self) -> List[VehicleRunner]:
        """
        Return all vehicle runners whose trips are not complete.
        """

        return [
            runner
            for runner in self._runners
            if not runner.is_complete()
        ]

    def start_all(
        self,
        now: Optional[datetime] = None,
    ) -> None:
        """
        Start every registered vehicle run.
        """

        for runner in self._runners:
            runner.start(now=now)

    def tick_all(
        self,
        now: Optional[datetime] = None,
    ) -> List[TelemetrySample]:
        """
        Advance every active vehicle by one simulation tick.

        Returns one TelemetrySample per active vehicle.
        """

        now = now or datetime.now(timezone.utc)

        samples: List[TelemetrySample] = []

        for runner in self.active_runners():
            sample = runner.tick(now=now)
            samples.append(sample)

        return samples

    def run(
        self,
        sink: TelemetrySink,
        max_ticks: Optional[int] = None,
        start_time: Optional[datetime] = None,
    ) -> None:
        """
        Run the entire fleet until all trips complete.

        Every generated TelemetrySample is forwarded to the
        provided sink.

        The sink may be:

            pipeline.publish

        or:

            analytics_engine.consume

        or:

            database_writer.consume

        or any other compatible telemetry consumer.
        """

        self.start_all(now=start_time)

        now = start_time or datetime.now(timezone.utc)
        ticks = 0

        while self.active_runners():

            samples = self.tick_all(now=now)

            for sample in samples:
                sink(sample)

            now += timedelta(seconds=self.tick_seconds)

            ticks += 1

            if max_ticks is not None and ticks >= max_ticks:
                break