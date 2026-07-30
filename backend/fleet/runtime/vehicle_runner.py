"""
Vehicle Runner.

Represents one active vehicle performing a trip. Owns the temporary
RuntimeState for that vehicle and drives the OBD generator tick by
tick, updating the persistent Vehicle (odometer, fuel level) and the
Trip (distance travelled, lifecycle status) as it goes.

The runner performs NO analytics: it does not rank the driver, judge
whether behavior is dangerous, calculate maintenance recommendations,
or access a database. It only produces telemetry and advances
state that belongs to the fleet/telemetry domain.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from backend.fleet.models.driver import Driver
from backend.fleet.models.route import Route
from backend.fleet.models.trip import Trip, TripStatus
from backend.fleet.models.vehicle import Vehicle
from backend.fleet.runtime.runtime_state import RuntimeState
from backend.telemetry.generators.obd_generator import OBDGenerator
from backend.telemetry.models.telemetry_sample import TelemetrySample

# Callback invoked with each generated sample. Kept as a simple
# function type rather than an event-bus/observer framework.
TelemetrySink = Callable[[TelemetrySample], None]


@dataclass
class VehicleRunner:
    vehicle: Vehicle
    driver: Driver
    route: Route
    trip: Trip

    runtime_state: RuntimeState = field(default_factory=RuntimeState)
    tick_seconds: float = 1.0
    run_seed: int = 0

    _generator: OBDGenerator = field(init=False)

    def __post_init__(self) -> None:
        vehicle_seed = self.run_seed + hash(self.vehicle.vehicle_id) & 0xFFFFFFFF
        self._generator = OBDGenerator(
            behavior_profile=self.driver.behavior_profile,
            seed=vehicle_seed,
        )

    def start(self, now: Optional[datetime] = None) -> None:
        self.trip.start(starting_odometer_km=self.vehicle.odometer_km, at=now)
        self.vehicle.start_engine()
        self.runtime_state.reset()

    def tick(self, now: Optional[datetime] = None) -> TelemetrySample:
        """
        Advance the simulation by one tick and return the telemetry
        sample produced. Raises if the trip is already completed.
        """
        if self.trip.status == TripStatus.COMPLETED:
            raise RuntimeError("Cannot tick a completed trip")

        now = now or datetime.utcnow()

        sample, distance_km, fuel_used_percent = self._generator.step(
            now=now,
            dt_seconds=self.tick_seconds,
            runtime_state=self.runtime_state,
            route=self.route,
            vehicle_id=self.vehicle.vehicle_id,
            driver_id=self.driver.driver_id,
            trip_id=self.trip.trip_id,
            vehicle_odometer_km=self.vehicle.odometer_km,
            vehicle_fuel_level_percent=self.vehicle.fuel_level_percent,
        )

        # Apply the tick's effects to persistent/lifecycle state.
        self.vehicle.advance_odometer(distance_km)
        self.vehicle.consume_fuel(fuel_used_percent)
        self.trip.advance(distance_km)

        if self.trip.is_complete(self.route.distance_km):
            self.trip.complete(ending_odometer_km=self.vehicle.odometer_km, at=now)
            self.vehicle.stop_engine()

        return sample

    def is_complete(self) -> bool:
        return self.trip.status == TripStatus.COMPLETED

    def run(
        self,
        sink: TelemetrySink,
        max_ticks: Optional[int] = None,
        start_time: Optional[datetime] = None,
    ) -> None:
        """
        Convenience loop: start the trip and tick until complete
        (or max_ticks is reached), sending each sample to `sink`.

        This is a simple synchronous loop, not a scheduler framework.
        Real-time/async pacing is left to the caller (e.g. FleetRunner
        or an API layer) since that concern doesn't belong here.
        """
        self.start(now=start_time)
        now = start_time or datetime.utcnow()
        ticks = 0

        while not self.is_complete():
            sample = self.tick(now=now)
            sink(sample)
            now = now + timedelta(seconds=self.tick_seconds)
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                break