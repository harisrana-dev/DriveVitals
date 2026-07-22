"""ContinuousRuntime: orchestrates the full Digital Twin pipeline.

Extends DigitalTwinRuntime with the complete simulation pipeline:
Decision → Controller → Physics → Sensors → Telemetry → Analytics.

Supports:
- Single deterministic ticks via step()
- Continuous real-time execution via run()
- Accelerated execution (no wall-clock delay)
- Graceful shutdown via stop()
- Pause/resume capability
- Multiple registered vehicles
- Driving scenarios for realistic vehicle behavior
- Structured TickResult output

The runtime does NOT own vehicle state. Vehicles remain the
authoritative domain objects. The runtime only orchestrates the
tick lifecycle and collects results.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from analytics.engine import AnalyticsEngine
from digital_twin.common.enums import DriverStatus, SimulationStatus
from digital_twin.common.exceptions import SimulationStateError
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.controller.vehicle_actuation import VehicleActuation
from digital_twin.decision.decision_context import DecisionContext
from digital_twin.decision.driver_behaviour_engine import DriverBehaviourEngine
from digital_twin.entities.driver import BehaviourProfile, Driver, ExperienceLevel
from digital_twin.entities.environment import EnvironmentSnapshot
from digital_twin.entities.trip import Trip
from digital_twin.entities.vehicle import Vehicle
from digital_twin.physics.physics_engine import PhysicsEngine, PhysicsTickResult
from digital_twin.runtime.digital_twin_runtime import DigitalTwinRuntime
from digital_twin.runtime.driving_scenario import DrivingScenario, create_scenario_for_vehicle
from digital_twin.runtime.tick_context import TickContext
from digital_twin.sensors.virtual_sensor_provider import VirtualSensorProvider
from digital_twin.telemetry.telemetry_generator import TelemetryGenerator
from digital_twin.telemetry.telemetry_packet import TelemetryPacket

# Lazy import to avoid circular dependency
from digital_twin.controller.vehicle_controller import VehicleController

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VehicleTickResult:
    """Result of processing one vehicle through one tick.

    Attributes:
        vehicle_id: Identifier of the vehicle.
        physics_result: Per-tick physics metrics.
        telemetry_packet: Immutable telemetry snapshot.
        analytics_result: Structured analytics output.
        error: Error message if processing failed, None otherwise.
    """

    vehicle_id: str
    physics_result: PhysicsTickResult | None = None
    telemetry_packet: TelemetryPacket | None = None
    analytics_result: dict | None = None
    error: str | None = None


@dataclass(frozen=True)
class TickResult:
    """Structured result of one complete simulation tick.

    Attributes:
        tick_id: Monotonically increasing tick counter.
        simulation_time: Simulated time after this tick.
        delta_time: Simulated seconds elapsed this tick.
        vehicle_results: Per-vehicle results, keyed by vehicle_id.
        errors: List of (vehicle_id, error_message) for failed vehicles.
    """

    tick_id: int
    simulation_time: datetime
    delta_time: float
    vehicle_results: dict[str, VehicleTickResult] = field(default_factory=dict)
    errors: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class _VehiclePipeline:
    """Per-vehicle pipeline state bundled together.

    Not a public type — internal bookkeeping so the runtime
    doesn't need parallel dictionaries.

    Attributes:
        vehicle: The authoritative Vehicle entity.
        driver: The Driver entity for this vehicle.
        sensor_provider: This vehicle's sensor observer.
        telemetry_generator: This vehicle's telemetry producer.
        decision_engine: The driver behaviour engine.
        vehicle_controller: The vehicle controller.
        scenario: Driving scenario for behavior generation.
        previous_actuation: Last actuation from controller.
        ticks_since_last_shift: Gear shift tracking.
        previous_oil_life_percent: Oil life carried from previous tick.
        trip: Current trip entity.
    """

    vehicle: Vehicle
    driver: Driver
    sensor_provider: VirtualSensorProvider
    telemetry_generator: TelemetryGenerator
    decision_engine: DriverBehaviourEngine
    vehicle_controller: "VehicleController"
    scenario: DrivingScenario
    previous_actuation: VehicleActuation | None = None
    ticks_since_last_shift: int = 999
    previous_oil_life_percent: float = 100.0
    trip: Trip | None = None


class ContinuousRuntime:
    """Orchestrates the full Digital Twin pipeline continuously.

    Composes DigitalTwinRuntime (for Sprint 1 manager orchestration)
    with Physics, Sensors, Telemetry, and Analytics layers.

    Usage:
        runtime = ContinuousRuntime(config)
        runtime.add_vehicle(vehicle)
        runtime.start()
        result = runtime.step()  # single tick
        runtime.run(100)         # 100 ticks
        runtime.stop()
    """

    def __init__(
        self,
        config: SimulationConfig | None = None,
    ) -> None:
        """Initialize the continuous runtime.

        Args:
            config: Simulation configuration. Uses defaults if omitted.
        """
        self._config = config or SimulationConfig()
        self._runtime = DigitalTwinRuntime(self._config)

        # Pipeline components (shared across vehicles)
        self._physics_engine = PhysicsEngine()
        self._analytics_engine = AnalyticsEngine()

        # Per-vehicle pipeline state
        self._pipelines: dict[str, _VehiclePipeline] = {}

        # Execution control
        self._running = False
        self._stop_requested = False
        self._stop_event = threading.Event()

    @property
    def status(self) -> SimulationStatus:
        """SimulationStatus: Current lifecycle state."""
        return self._runtime.status

    @property
    def tick_id(self) -> int:
        """int: Current tick counter."""
        return self._runtime.clock.tick_id

    @property
    def simulation_time(self) -> datetime:
        """datetime: Current simulated time."""
        return self._runtime.clock.current_time

    @property
    def clock(self):
        """SimulationClock: The underlying simulation clock."""
        return self._runtime.clock

    @property
    def config(self) -> SimulationConfig:
        """SimulationConfig: The configuration this runtime uses."""
        return self._config

    # --- Vehicle management ---

    def add_vehicle(
        self,
        vehicle: Vehicle,
        driver: Driver | None = None,
        sensor_provider: VirtualSensorProvider | None = None,
        telemetry_generator: TelemetryGenerator | None = None,
        scenario: DrivingScenario | None = None,
        seed: int = 0,
        index: int = 0,
    ) -> None:
        """Register a vehicle for simulation processing.

        Args:
            vehicle: The authoritative Vehicle entity.
            driver: Optional Driver entity. Creates a default if omitted.
            sensor_provider: Optional pre-built sensor provider.
            telemetry_generator: Optional pre-built telemetry generator.
            scenario: Optional driving scenario. Creates a default if omitted.
            seed: Random seed for deterministic scenarios.
            index: Vehicle index for scenario variation.

        Raises:
            ValueError: If vehicle_id is empty or already registered.
        """
        if not vehicle.vehicle_id:
            raise ValueError("Vehicle ID cannot be empty.")
        if vehicle.vehicle_id in self._pipelines:
            raise ValueError(f"Vehicle '{vehicle.vehicle_id}' is already registered.")

        if driver is None:
            driver = Driver(
                driver_id=f"driver-{vehicle.vehicle_id[-3:]}",
                name=f"Driver {vehicle.vehicle_id}",
                license_number=f"LIC-{vehicle.vehicle_id[-3:]}",
                behaviour_profile=BehaviourProfile.STANDARD,
                experience_level=ExperienceLevel.EXPERIENCED,
                status=DriverStatus.ON_TRIP,
            )

        if scenario is None:
            scenario = create_scenario_for_vehicle(
                vehicle.vehicle_id, seed=seed, index=index,
            )

        self._pipelines[vehicle.vehicle_id] = _VehiclePipeline(
            vehicle=vehicle,
            driver=driver,
            sensor_provider=sensor_provider or VirtualSensorProvider(),
            telemetry_generator=telemetry_generator or TelemetryGenerator(),
            decision_engine=DriverBehaviourEngine(),
            vehicle_controller=VehicleController(),
            scenario=scenario,
        )
        logger.info("Registered vehicle: %s", vehicle.vehicle_id)

    def remove_vehicle(self, vehicle_id: str) -> None:
        """Unregister a vehicle from simulation processing.

        Args:
            vehicle_id: Id of the vehicle to remove.

        Raises:
            ValueError: If vehicle_id is not registered.
        """
        if vehicle_id not in self._pipelines:
            raise ValueError(f"Vehicle '{vehicle_id}' is not registered.")
        del self._pipelines[vehicle_id]
        logger.info("Removed vehicle: %s", vehicle_id)

    def get_vehicle(self, vehicle_id: str) -> Vehicle | None:
        """Return a registered Vehicle by id, or None."""
        pipeline = self._pipelines.get(vehicle_id)
        return pipeline.vehicle if pipeline else None

    def get_all_vehicles(self) -> dict[str, Vehicle]:
        """Return all registered vehicles, keyed by vehicle_id."""
        return {vid: p.vehicle for vid, p in self._pipelines.items()}

    # --- Lifecycle ---

    def start(self) -> None:
        """Start the simulation runtime.

        Raises:
            SimulationStateError: If already running.
        """
        self._runtime.start()
        self._running = True
        self._stop_requested = False
        self._stop_event.clear()
        logger.info("ContinuousRuntime started.")

    def stop(self) -> None:
        """Request graceful shutdown. Finishes current tick then exits."""
        if self._runtime.status != SimulationStatus.RUNNING:
            return
        self._stop_requested = True
        self._stop_event.wait(timeout=5.0)
        self._runtime.stop()
        logger.info("ContinuousRuntime stopped.")

    def pause(self) -> None:
        """Pause the simulation.

        Raises:
            SimulationStateError: If not running.
        """
        self._runtime.pause()
        logger.info("ContinuousRuntime paused.")

    def resume(self) -> None:
        """Resume a paused simulation.

        Raises:
            SimulationStateError: If not paused.
        """
        self._runtime.resume()
        logger.info("ContinuousRuntime resumed.")

    def reset(self, start_time: datetime | None = None) -> None:
        """Reset the runtime to initial state.

        Args:
            start_time: Optional new simulated start time.
        """
        self._runtime.reset(start_time=start_time)
        self._running = False
        self._stop_requested = False
        self._stop_event.clear()
        # Reset pipeline state for all vehicles
        for pipeline in self._pipelines.values():
            pipeline.previous_oil_life_percent = 100.0
            pipeline.previous_actuation = None
            pipeline.ticks_since_last_shift = 999
        logger.info("ContinuousRuntime reset.")

    # --- Core tick ---

    def step(self) -> TickResult:
        """Execute exactly one simulation tick through the full pipeline.

        The pipeline per vehicle:
            1. Advance physics
            2. Read sensors
            3. Generate telemetry
            4. Process analytics

        Returns:
            Structured TickResult with per-vehicle outcomes.

        Raises:
            SimulationStateError: If not running.
        """
        if self._runtime.status != SimulationStatus.RUNNING:
            raise SimulationStateError("Cannot step: runtime is not running.")

        # 1. Advance clock and run Sprint 1 managers
        tick_context = self._runtime.run_tick()

        # 2. Process each vehicle through the full pipeline
        vehicle_results: dict[str, VehicleTickResult] = {}
        errors: list[tuple[str, str]] = []

        for vid, pipeline in self._pipelines.items():
            try:
                vtr = self._process_vehicle_tick(pipeline, tick_context)
                vehicle_results[vid] = vtr
                if vtr.error:
                    errors.append((vid, vtr.error))
            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                vehicle_results[vid] = VehicleTickResult(
                    vehicle_id=vid, error=error_msg,
                )
                errors.append((vid, error_msg))
                logger.error("Vehicle %s failed: %s", vid, exc)

        return TickResult(
            tick_id=tick_context.tick_id,
            simulation_time=tick_context.simulation_time,
            delta_time=tick_context.delta_time,
            vehicle_results=vehicle_results,
            errors=errors,
        )

    def _process_vehicle_tick(
        self,
        pipeline: _VehiclePipeline,
        tick_context: TickContext,
    ) -> VehicleTickResult:
        """Process one vehicle through Decision → Controller → Physics → Sensors → Telemetry → Analytics.

        Args:
            pipeline: Per-vehicle pipeline state.
            tick_context: The current tick's context.

        Returns:
            VehicleTickResult with all per-tick outputs.
        """
        vehicle = pipeline.vehicle
        driver = pipeline.driver

        # 1. Get driving command from scenario
        driving_command = pipeline.scenario.tick(vehicle.state.current_speed_kmh)

        # 2. Build DecisionContext
        environment = EnvironmentSnapshot(
            current_time=tick_context.simulation_time,
        )

        decision_context = DecisionContext(
            driver=driver,
            vehicle=vehicle,
            trip=pipeline.trip,
            route=None,
            cargo=None,
            environment=environment,
            tick_context=tick_context,
            current_speed_kmh=vehicle.state.current_speed_kmh,
            current_fatigue_level=driver.fatigue_level,
            current_speed_limit_kmh=120.0,
            continuous_driving_hours=driver.continuous_work_hours,
            break_duration_minutes=driver.break_time_minutes,
            shift_duration_hours=(tick_context.tick_id * tick_context.delta_time) / 3600.0,
        )

        # 3. Decision Layer
        intent = pipeline.decision_engine.decide(decision_context)

        # Override intent with scenario target speed
        # The scenario provides the behavioral intent, the decision engine
        # provides fatigue/safety overrides. We use the scenario's target
        # speed as the primary goal.
        from digital_twin.decision.driver_intent import DriverIntent
        intent = DriverIntent(
            target_speed_kmh=driving_command.target_speed_kmh,
            desired_acceleration_mps2=driving_command.throttle * 2.5 - driving_command.brake * 6.0,
            throttle_request=driving_command.throttle,
            brake_request=driving_command.brake,
            steering_request=0.0,
            request_stop=driving_command.state.value in ("STOPPED", "IDLE"),
            request_emergency_stop=False,
            request_lane_change=False,
            overtake_requested=False,
            reason=driving_command.reason,
            decision_timestamp=tick_context.simulation_time,
        )

        # 4. Vehicle Controller
        actuation = pipeline.vehicle_controller.compute_actuation(
            intent=intent,
            vehicle=vehicle,
            tick_context=tick_context,
            previous_actuation=pipeline.previous_actuation,
            ticks_since_last_shift=pipeline.ticks_since_last_shift,
        )

        # Track gear shifts
        if (
            pipeline.previous_actuation is None
            or actuation.requested_gear != pipeline.previous_actuation.requested_gear
        ):
            pipeline.ticks_since_last_shift = 0
        else:
            pipeline.ticks_since_last_shift += 1
        pipeline.previous_actuation = actuation

        # 5. Physics Engine
        physics_result = self._physics_engine.update(
            vehicle=vehicle,
            actuation=actuation,
            environment=environment,
            tick_context=tick_context,
            previous_oil_life_percent=pipeline.previous_oil_life_percent,
        )
        pipeline.previous_oil_life_percent = physics_result.oil_life_percent

        # 6. Sensors
        sensor_readings = pipeline.sensor_provider.update_all(
            vehicle, tick_context,
        )

        # 7. Telemetry
        telemetry_packet = pipeline.telemetry_generator.generate(
            vehicle, sensor_readings, tick_context,
        )

        # 8. Analytics
        analytics_result = self._analytics_engine.process(telemetry_packet)

        return VehicleTickResult(
            vehicle_id=vehicle.vehicle_id,
            physics_result=physics_result,
            telemetry_packet=telemetry_packet,
            analytics_result=analytics_result,
        )

    # --- Continuous execution ---

    def run(
        self,
        num_ticks: int | None = None,
        real_time: bool = False,
    ) -> None:
        """Run the simulation continuously.

        Args:
            num_ticks: Number of ticks to execute. If None, runs
                indefinitely until stop() is called.
            real_time: If True, maintain approximately real-time
                pacing between ticks. If False, run as fast as possible.

        Raises:
            SimulationStateError: If not running.
        """
        if self._runtime.status != SimulationStatus.RUNNING:
            raise SimulationStateError("Cannot run: runtime is not running.")

        self._running = True
        self._stop_requested = False
        tick_count = 0

        while self._running:
            if self._stop_requested:
                break
            if num_ticks is not None and tick_count >= num_ticks:
                break

            tick_start = time.perf_counter()
            self.step()
            tick_count += 1

            if real_time:
                elapsed = time.perf_counter() - tick_start
                remaining = max(
                    0,
                    self._config.clock.tick_interval_seconds - elapsed,
                )
                if remaining > 0:
                    time.sleep(remaining)

        self._running = False
        self._runtime.stop()
        self._stop_event.set()
        logger.info("ContinuousRuntime run completed after %d ticks.", tick_count)

    async def run_async(
        self,
        num_ticks: int | None = None,
        real_time: bool = False,
    ) -> None:
        """Run the simulation continuously without blocking the event loop.

        Args:
            num_ticks: Number of ticks to execute. If None, runs
                indefinitely until stop() is called.
            real_time: If True, maintain approximately real-time pacing.
        """
        if self._runtime.status != SimulationStatus.RUNNING:
            raise SimulationStateError("Cannot run: runtime is not running.")

        self._running = True
        self._stop_requested = False
        tick_count = 0

        while self._running:
            if self._stop_requested:
                break
            if num_ticks is not None and tick_count >= num_ticks:
                break

            tick_start = time.perf_counter()
            self.step()
            tick_count += 1

            if real_time:
                elapsed = time.perf_counter() - tick_start
                remaining = max(
                    0,
                    self._config.clock.tick_interval_seconds - elapsed,
                )
                if remaining > 0:
                    await asyncio.sleep(remaining)

        self._running = False
        self._stop_event.set()
        logger.info("ContinuousRuntime async run completed after %d ticks.", tick_count)
