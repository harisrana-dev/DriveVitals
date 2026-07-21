"""SimulationRunner: the application composition root for DriveVitals.

Wires together the existing, frozen layers (DigitalTwinRuntime +
Managers, Decision Layer, Vehicle Controller, Physics Engine, Virtual
Sensors, Telemetry) into a runnable multi-vehicle fleet simulation.
Contains no physics, driver-behavior, sensor, or telemetry-formatting
logic of its own -- every one of those responsibilities is delegated
to its existing module. See `entity_bridge.py` for the one genuinely
new piece: the small adapter resolving the Sprint 1 <-> Sprint 2+
data-model gap (full report in that module's docstring).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from digital_twin.common.enums import (
    DriverStatus,
    RoadCondition,
    TripStatus,
    VehicleStatus,
    WeatherCondition,
)
from digital_twin.config.defaults import create_default_simulation_config
from digital_twin.controller.vehicle_actuation import VehicleActuation
from digital_twin.controller.vehicle_controller import VehicleController
from digital_twin.decision.decision_context import DecisionContext
from digital_twin.decision.driver_behaviour_engine import DriverBehaviourEngine
from digital_twin.entities.driver import BehaviourProfile, Driver, ExperienceLevel
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.trip import Trip
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.managers.dispatch_manager import DispatchManager
from digital_twin.managers.driver_manager import DriverManager
from digital_twin.managers.environment_manager import EnvironmentManager
from digital_twin.managers.fleet_manager import FleetManager
from digital_twin.managers.maintenance_manager import MaintenanceManager
from digital_twin.managers.trip_manager import TripManager
from digital_twin.managers.vehicle_manager import VehicleManager
from digital_twin.physics.physics_engine import PhysicsEngine
from digital_twin.runtime.digital_twin_runtime import DigitalTwinRuntime
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors.sensor_models import SensorReading
from digital_twin.sensors.virtual_sensor_provider import VirtualSensorProvider
from digital_twin.simulation.entity_bridge import (
    bridge_environment_snapshot,
    compute_break_duration_minutes,
    compute_continuous_driving_hours,
    compute_shift_duration_hours,
)
from digital_twin.telemetry.telemetry_generator import TelemetryGenerator
from digital_twin.telemetry.telemetry_packet import TelemetryPacket
from digital_twin.telemetry.telemetry_pipeline import TelemetryPipeline
from digital_twin.telemetry.telemetry_stream import InMemoryTelemetryStream, TelemetryStream

#: Deterministic cycle of behaviour profiles applied to drivers in
#: order, wrapping if fleet_size exceeds the cycle length. Uses the
#: existing `BehaviourProfile` enum (Decision Layer, unmodified) --
#: no new behavior categories are invented.
_BEHAVIOUR_PROFILE_CYCLE: tuple[BehaviourProfile, ...] = (
    BehaviourProfile.AGGRESSIVE,
    BehaviourProfile.STANDARD,
    BehaviourProfile.CAUTIOUS,
    BehaviourProfile.ECO_FOCUSED,
)


@dataclass(frozen=True)
class RunnerConfig:
    """Configuration for a SimulationRunner instance.

    Attributes:
        fleet_size: Number of vehicles (and drivers, and driver-vehicle
            assignments) to create.
        num_ticks: Number of ticks to run.
        real_time_pacing: If True, sleep between ticks so the run
            paces itself against real wall-clock time (useful for
            manual observation); if False, ticks run back-to-back.
        random_seed: Seed threaded into `EnvironmentManagerConfig` and
            the runner's own config, for reproducibility. Never used
            to introduce randomness into any decision -- see
            `digital_twin.decision` and `digital_twin.physics` for the
            "no random()" guarantees those layers already provide.
        weather: The fixed weather condition applied to the
            EnvironmentManager at startup.
        road_condition: The fixed road condition applied to the
            EnvironmentManager at startup.
        speed_limit_kmh: The speed limit supplied to the Decision
            Layer for every vehicle. There is no per-route speed limit
            source wired into this runner (no `Route` entity is built
            per vehicle -- see the class docstring on `SimulationRunner`
            for why), so a single fleet-wide limit is used.
    """

    fleet_size: int = 3
    num_ticks: int = 10
    real_time_pacing: bool = False
    random_seed: int = 42
    weather: WeatherCondition = WeatherCondition.CLEAR
    road_condition: RoadCondition = RoadCondition.NORMAL
    speed_limit_kmh: float = 90.0


@dataclass
class _VehicleUnit:
    """Per-vehicle state the runner threads across ticks.

    Not a public type -- an internal bookkeeping bundle so
    `SimulationRunner` doesn't need six parallel dictionaries. Holds
    exactly the state each existing component's own API already
    requires the caller to carry forward (e.g. `VehicleController`
    needs the previous tick's `VehicleActuation`; `PhysicsEngine` needs
    the previous tick's oil life) -- nothing here duplicates logic
    those components own.

    Attributes:
        vehicle_id: This unit's vehicle id.
        driver_id: This unit's driver id.
        vehicle_entity: The Vehicle entity simulated for this vehicle.
        driver_entity: The Driver entity simulated for this vehicle.
        trip_entity: The Trip entity this vehicle/driver are working.
        sensor_provider: This vehicle's own VirtualSensorProvider.
        telemetry_generator: This vehicle's own TelemetryGenerator (and
            therefore its own independent sequence-number counter).
        previous_actuation: The last VehicleActuation computed, or
            None before the first tick.
        ticks_since_last_shift: Ticks elapsed since the transmission
            last changed gear, for GearLogic's shift-interval/hunting
            protection.
        previous_oil_life_percent: The last oil life value from
            PhysicsEngine, threaded forward each tick (see the Physics
            Engine's own interface mismatch report for why this can't
            simply live on VehicleState).
        last_packet: The most recently generated TelemetryPacket, kept
            for the runner's own summary printing.
    """

    vehicle_id: str
    driver_id: str
    vehicle_entity: Vehicle
    driver_entity: Driver
    trip_entity: Trip
    sensor_provider: VirtualSensorProvider
    telemetry_generator: TelemetryGenerator
    previous_actuation: VehicleActuation | None = None
    ticks_since_last_shift: int = 999
    previous_oil_life_percent: float = 100.0
    last_packet: TelemetryPacket | None = None


class SimulationRunner:
    """Composition root: wires the full pipeline for a multi-vehicle fleet.

    Constructs and owns one `DigitalTwinRuntime` (with the standard
    Sprint 1 managers registered in their frozen execution order), and
    one full Decision/Controller/Physics/Sensors/Telemetry stack per
    vehicle. Every tick:

        1. `DigitalTwinRuntime.run_tick()` advances the clock and runs
           Environment -> Dispatch -> Drivers -> Vehicles -> Trips ->
           Maintenance, exactly as Sprint 1 defines it.
        2. For each vehicle, this runner builds a `DecisionContext` and
           calls the *existing* `DriverBehaviourEngine`, then
           `VehicleController`, then `PhysicsEngine`, then
           `VirtualSensorProvider`, then `TelemetryGenerator` and
           `TelemetryPipeline` -- in that fixed order, using each
           component's real public API.

    No Route or Cargo entity is built per vehicle for this sprint (both
    are optional on `DecisionContext`); a fleet-wide `speed_limit_kmh`
    stands in for a per-route limit, since no route-to-position
    resolution exists anywhere in the current architecture to source
    one from. This is a scope simplification, not a fabricated value.
    """

    def __init__(
        self,
        config: RunnerConfig | None = None,
        stream: TelemetryStream | None = None,
    ) -> None:
        """Initialize the runner and build its configured fleet.

        Args:
            config: Runner configuration. Defaults to `RunnerConfig()`
                (a 3-vehicle, 10-tick, CLEAR-weather fleet).
            stream: The TelemetryStream every vehicle's
                TelemetryPipeline forwards packets to. Defaults to a
                new, shared `InMemoryTelemetryStream` -- one stream for
                the whole fleet, with packets attributed by
                `vehicle_id`, matching how a real telemetry bus (one
                topic/table, filtered by vehicle) would work.
        """
        self._config = config or RunnerConfig()

        self._sim_config = create_default_simulation_config()
        self._runtime = DigitalTwinRuntime(self._sim_config)

        self._vehicle_manager = VehicleManager()
        self._driver_manager = DriverManager(self._sim_config.driver)
        self._trip_manager = TripManager()
        self._dispatch_manager = DispatchManager(
            self._driver_manager, self._vehicle_manager, self._trip_manager
        )
        self._maintenance_manager = MaintenanceManager(self._sim_config.maintenance)
        self._environment_manager = EnvironmentManager(self._sim_config.environment)
        self._fleet_manager = FleetManager(
            self._sim_config.fleet,
            self._driver_manager,
            self._vehicle_manager,
            self._trip_manager,
        )

        for manager in (
            self._environment_manager,
            self._dispatch_manager,
            self._driver_manager,
            self._vehicle_manager,
            self._trip_manager,
            self._maintenance_manager,
        ):
            self._runtime.register_manager(manager)

        self._environment_manager.set_weather(self._config.weather)
        self._environment_manager.set_road_condition(self._config.road_condition)

        self._decision_engine = DriverBehaviourEngine()
        self._vehicle_controller = VehicleController()
        self._physics_engine = PhysicsEngine()
        self._stream = stream or InMemoryTelemetryStream()
        self._telemetry_pipeline = TelemetryPipeline(stream=self._stream)

        self._vehicle_units: dict[str, _VehicleUnit] = {}
        self._build_fleet()

    @property
    def stream(self) -> TelemetryStream:
        """TelemetryStream: The shared stream every vehicle publishes to."""
        return self._stream

    @property
    def vehicle_ids(self) -> list[str]:
        """list[str]: Ids of every vehicle in this runner's fleet, in order."""
        return list(self._vehicle_units.keys())

    def _build_fleet(self) -> None:
        """Onboard vehicles/drivers/trips into Sprint 1 managers and build entities.

        For each vehicle index, this registers a `VehicleRecord` and
        `DriverRecord` with the existing `FleetManager` (unmodified
        Sprint 1 API), creates a pending `TripRecord`, and separately
        builds the `Vehicle`/`Driver`/`Trip` entities the downstream
        Decision/Controller/Physics/Sensors/Telemetry stack requires --
        per the integration gap documented in `entity_bridge.py`.
        """
        start_time = self._runtime.clock.current_time

        for index in range(1, self._config.fleet_size + 1):
            vehicle_id = f"vehicle-{index:03d}"
            driver_id = f"driver-{index:03d}"
            trip_id = f"trip-{index:03d}"

            self._fleet_manager.onboard_vehicle(vehicle_id, vehicle_type="delivery_van")
            self._fleet_manager.onboard_driver(driver_id, name=f"Driver {index:03d}")
            self._fleet_manager.create_trip(
                trip_id,
                origin="Depot",
                destination=f"Customer {index:03d}",
                created_at=start_time,
            )

            behaviour_profile = _BEHAVIOUR_PROFILE_CYCLE[
                (index - 1) % len(_BEHAVIOUR_PROFILE_CYCLE)
            ]

            vehicle_entity = Vehicle(
                vehicle_id=vehicle_id,
                vin=f"VIN{index:09d}",
                specification=VehicleSpecification(
                    manufacturer="Ford",
                    model="Transit",
                    year=2022,
                    fuel_type=FuelType.DIESEL,
                    transmission=TransmissionType.AUTOMATIC,
                ),
                current_driver_id=driver_id,
                current_trip_id=trip_id,
                status=VehicleStatus.ON_TRIP,
            )
            driver_entity = Driver(
                driver_id=driver_id,
                name=f"Driver {index:03d}",
                license_number=f"LIC-{index:06d}",
                behaviour_profile=behaviour_profile,
                experience_level=ExperienceLevel.EXPERIENCED,
                current_vehicle_id=vehicle_id,
                current_trip_id=trip_id,
                status=DriverStatus.ON_TRIP,
            )
            trip_entity = Trip(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                status=TripStatus.IN_PROGRESS,
                distance_planned_km=50.0,
            )

            self._vehicle_units[vehicle_id] = _VehicleUnit(
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                vehicle_entity=vehicle_entity,
                driver_entity=driver_entity,
                trip_entity=trip_entity,
                sensor_provider=VirtualSensorProvider(),
                telemetry_generator=TelemetryGenerator(),
            )

    def start(self) -> None:
        """Start the underlying DigitalTwinRuntime."""
        self._runtime.start()

    def run(self) -> None:
        """Run the full configured simulation (start + all ticks)."""
        self.start()
        for _ in range(self._config.num_ticks):
            self.run_tick()
            if self._config.real_time_pacing:
                time.sleep(self._sim_config.clock.tick_interval_seconds)

    def run_tick(self) -> TickContext:
        """Advance one full tick: Sprint 1 managers, then every vehicle's pipeline.

        Returns:
            The TickContext produced by `DigitalTwinRuntime.run_tick()`
            for this tick.
        """
        tick_context = self._runtime.run_tick()
        environment_snapshot = bridge_environment_snapshot(
            self._environment_manager.state, tick_context
        )

        for unit in self._vehicle_units.values():
            self._simulate_vehicle_tick(unit, tick_context, environment_snapshot)

        return tick_context

    def _simulate_vehicle_tick(
        self,
        unit: _VehicleUnit,
        tick_context: TickContext,
        environment_snapshot: EnvironmentSnapshot,
    ) -> None:
        """Run one vehicle through Decision -> Controller -> Physics -> Sensors -> Telemetry.

        Args:
            unit: The vehicle's per-vehicle state bundle.
            tick_context: The current tick's context.
            environment_snapshot: This tick's bridged EnvironmentSnapshot.
        """
        driver_record = self._driver_manager.get_driver(unit.driver_id)

        decision_context = DecisionContext(
            driver=unit.driver_entity,
            vehicle=unit.vehicle_entity,
            trip=unit.trip_entity,
            route=None,
            cargo=None,
            environment=environment_snapshot,
            tick_context=tick_context,
            current_speed_kmh=unit.vehicle_entity.state.current_speed_kmh,
            current_fatigue_level=unit.driver_entity.fatigue_level,
            current_speed_limit_kmh=self._config.speed_limit_kmh,
            continuous_driving_hours=compute_continuous_driving_hours(driver_record),
            break_duration_minutes=compute_break_duration_minutes(
                driver_record, self._sim_config.driver.mandatory_break_minutes
            ),
            shift_duration_hours=compute_shift_duration_hours(tick_context),
        )

        intent = self._decision_engine.decide(decision_context)
        print("\n" + "=" * 80)
        print(f"TICK {tick_context.tick_id} | VEHICLE {unit.vehicle_id}")
        print("=" * 80)

        print("\n[1] TICK CONTEXT")
        print(tick_context)

        print("\n[2] ENVIRONMENT SNAPSHOT")
        print(environment_snapshot)

        print("\n[3] DECISION CONTEXT")
        print(decision_context)

        print("\n[4] DRIVER INTENT")
        print(intent)

        actuation = self._vehicle_controller.compute_actuation(
            intent=intent,
            vehicle=unit.vehicle_entity,
            tick_context=tick_context,
            previous_actuation=unit.previous_actuation,
            ticks_since_last_shift=unit.ticks_since_last_shift,
        )
        print("\n[5] VEHICLE ACTUATION")
        print(actuation)
        if (
            unit.previous_actuation is None
            or actuation.requested_gear != unit.previous_actuation.requested_gear
        ):
            unit.ticks_since_last_shift = 0
        else:
            unit.ticks_since_last_shift += 1
        unit.previous_actuation = actuation

        physics_result = self._physics_engine.update(
            vehicle=unit.vehicle_entity,
            actuation=actuation,
            environment=environment_snapshot,
            tick_context=tick_context,
            previous_oil_life_percent=unit.previous_oil_life_percent,
        )
        unit.previous_oil_life_percent = physics_result.oil_life_percent

        # Accumulate physics results into the active Trip entity.
        trip = unit.trip_entity
        trip.distance_completed_km += physics_result.distance_travelled_km
        trip.fuel_consumed_liters += physics_result.fuel_consumed_liters
        trip.duration_minutes += tick_context.delta_time / 60.0
        if trip.fuel_consumed_liters > 0:
            trip.fuel_efficiency_km_per_liter = (
                trip.distance_completed_km / trip.fuel_consumed_liters
            )
        if trip.duration_minutes > 0:
            trip.average_speed_kmh = (
                trip.distance_completed_km / trip.duration_minutes
            ) * 60.0

        print("\n[6] PHYSICS RESULT")
        print(physics_result)

        print("\n[6a] TRIP PROGRESS")
        print(
            f"  distance_completed_km={trip.distance_completed_km:.6f} | "
            f"fuel_consumed_liters={trip.fuel_consumed_liters:.6f} | "
            f"duration_minutes={trip.duration_minutes:.6f} | "
            f"average_speed_kmh={trip.average_speed_kmh:.6f} | "
            f"fuel_efficiency_km_per_liter={trip.fuel_efficiency_km_per_liter:.6f}"
        )

        print("\n[7] VEHICLE STATE AFTER PHYSICS")
        print(unit.vehicle_entity.state)

        readings: list[SensorReading] = unit.sensor_provider.update_all(
            unit.vehicle_entity, tick_context
        )
        print("\n[8] SENSOR READINGS")
        for reading in readings:
            print(f"  {reading}")
        packet = unit.telemetry_generator.generate(
            unit.vehicle_entity, readings, tick_context
        )
        print("\n[9] TELEMETRY PACKET")
        print(packet)
        unit.last_packet = self._telemetry_pipeline.process(packet)
        print("\n[10] PACKET AFTER TELEMETRY PIPELINE")
        print(unit.last_packet)

        print("\n[11] STREAM")
        print(f"Packets currently in stream: {len(self._stream.recent())}")

    def current_speed_kmh(self, vehicle_id: str) -> float:
        """Return a vehicle's current speed.

        Args:
            vehicle_id: Id of the vehicle to query.

        Returns:
            The vehicle's current speed, in km/h.
        """
        return self._vehicle_units[vehicle_id].vehicle_entity.state.current_speed_kmh

    def vehicle_state_summary(self, vehicle_id: str) -> str:
        """Build a one-line human-readable summary of a vehicle's current state.

        Args:
            vehicle_id: Id of the vehicle to summarize.

        Returns:
            A string like "vehicle-001 | driver-001 | speed=42.31 km/h
            | rpm=2103 | gear=3".
        """
        unit = self._vehicle_units[vehicle_id]
        state = unit.vehicle_entity.state
        return (
            f"{unit.vehicle_id} | {unit.driver_id} | "
            f"speed={state.current_speed_kmh:6.2f} km/h | "
            f"rpm={state.current_rpm:5.0f} | "
            f"gear={state.current_gear:2d}"
        )


def main() -> None:
    """Run a default 3-vehicle simulation, for `python -m digital_twin.simulation.simulation_runner`.

    For the full demo output (fleet summary, per-tick printout,
    telemetry summary, and validation checks), run
    `run_simulation.py` at the project root instead -- this is the
    minimal entry point satisfying "runnable via python -m".
    """
    runner = SimulationRunner()
    runner.run()
    for vehicle_id in runner.vehicle_ids:
        print(runner.vehicle_state_summary(vehicle_id))
    print(f"Total packets published: {len(runner.stream.recent())}")


if __name__ == "__main__":
    main()