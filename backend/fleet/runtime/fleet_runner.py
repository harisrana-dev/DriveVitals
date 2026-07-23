"""
Fleet Runner.

Coordinates multiple VehicleRunner instances so several
vehicle/driver/route assignments can operate independently at the
same time (target scale: roughly 10 vehicles / 10 drivers).

This is intentionally a simple loop-based coordinator — not a
distributed systems architecture or scheduler framework. Each
VehicleRunner advances independently; the FleetRunner just ticks all
of them that are still active and forwards their telemetry to a
single sink.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
        Register a new active vehicle run for the given assignment.
        Returns the created VehicleRunner in case the caller wants to
        inspect it directly.
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
        return [r for r in self._runners if not r.is_complete()]

    def start_all(self, now: Optional[datetime] = None) -> None:
        for runner in self._runners:
            runner.start(now=now)

    def tick_all(self, now: Optional[datetime] = None) -> List[TelemetrySample]:
        """
        Advance every still-active vehicle by one tick and return the
        telemetry samples generated this tick (order matches
        `active_runners()` at call time).
        """
        now = now or datetime.utcnow()
        samples = []
        for runner in self.active_runners():
            samples.append(runner.tick(now=now))
        return samples

    def run(
        self,
        sink: TelemetrySink,
        max_ticks: Optional[int] = None,
        start_time: Optional[datetime] = None,
    ) -> None:
        """
        Start every registered run and tick the whole fleet forward
        until all trips are complete (or max_ticks is reached),
        forwarding every sample to `sink`.
        """
        self.start_all(now=start_time)
        now = start_time or datetime.utcnow()
        ticks = 0

        while self.active_runners():
            for sample in self.tick_all(now=now):
                sink(sample)
            now = now + timedelta(seconds=self.tick_seconds)
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                break