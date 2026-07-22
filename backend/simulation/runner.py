"""Production SimulationRunner: continuously executes the Digital Twin.

Bridges the ContinuousRuntime (Digital Twin execution pipeline) with
external consumers (database, WebSocket, analytics) through clean
sink interfaces.

Architecture:

    ContinuousRuntime
        ↓
    TickResult
        ↓
    SimulationRunner
        ├── TelemetrySink(s)
        ├── AnalyticsSink(s)
        ├── EventSink(s)
        └── LiveUpdateSink(s)

The runner is responsible for:
- Creating and configuring the ContinuousRuntime
- Executing the simulation loop
- Dispatching results to registered sinks
- Graceful lifecycle management (start/stop/pause/resume)
- Real-time pacing with monotonic clock scheduling
- Concise terminal output for live observation

The runner does NOT own vehicle state, physics, sensors, telemetry,
or analytics. Those remain the responsibility of the Digital Twin core.
"""

from __future__ import annotations

import logging
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from digital_twin.common.enums import SimulationStatus, VehicleStatus
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.entities.vehicle import (
    FuelType,
    TransmissionType,
    Vehicle,
    VehicleSpecification,
)
from digital_twin.runtime.continuous_runtime import ContinuousRuntime, TickResult
from simulation.sinks import (
    AnalyticsSink,
    EventSink,
    LiveUpdateSink,
    TelemetrySink,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunnerConfig:
    """Configuration for the SimulationRunner.

    Attributes:
        fleet_size: Number of vehicles to create.
        real_time: If True, pace ticks to approximately 1/second.
        num_ticks: Number of ticks to run. None = infinite.
        start_time: Simulated start time. None = now.
        speed_limit_kmh: Fleet-wide speed limit for vehicles.
        real_time_interval: Target seconds between ticks in real-time mode.
    """

    fleet_size: int = 3
    real_time: bool = True
    num_ticks: int | None = None
    start_time: datetime | None = None
    speed_limit_kmh: float = 90.0
    real_time_interval: float = 1.0


@dataclass
class SimulationStats:
    """Accumulated simulation statistics.

    Attributes:
        ticks_completed: Total ticks executed.
        telemetry_packets_generated: Total telemetry packets sent to sinks.
        analytics_executions: Total analytics results sent to sinks.
        events_generated: Total events sent to event sinks.
        start_wall_time: Wall-clock time when simulation started.
        errors: List of (tick_id, vehicle_id, error_message) tuples.
    """

    ticks_completed: int = 0
    telemetry_packets_generated: int = 0
    analytics_executions: int = 0
    events_generated: int = 0
    start_wall_time: float = 0.0
    errors: list[tuple[int, str, str]] = field(default_factory=list)


class SimulationRunner:
    """Production simulation runner with sink-based integration.

    Creates vehicles, registers them with a ContinuousRuntime,
    and executes the simulation loop. Results are dispatched to
    registered sinks for persistence, live updates, and analytics.

    Usage:
        runner = SimulationRunner(RunnerConfig(fleet_size=5))
        runner.add_telemetry_sink(MyDatabaseSink())
        runner.add_analytics_sink(MyAnalyticsSink())
        runner.start()  # runs until stop() or Ctrl+C
    """

    def __init__(
        self,
        config: RunnerConfig | None = None,
    ) -> None:
        """Initialize the simulation runner.

        Args:
            config: Runner configuration. Uses defaults if omitted.
        """
        self._config = config or RunnerConfig()
        self._sim_config = SimulationConfig()

        # Runtime
        self._runtime = ContinuousRuntime(self._sim_config)

        # Sinks
        self._telemetry_sinks: list[TelemetrySink] = []
        self._analytics_sinks: list[AnalyticsSink] = []
        self._event_sinks: list[EventSink] = []
        self._live_update_sinks: list[LiveUpdateSink] = []

        # State
        self._running = False
        self._stop_requested = False
        self._stats = SimulationStats()
        self._stop_event = threading.Event()

        # Signal handling
        self._original_sigint = None
        self._original_sigterm = None

    @property
    def status(self) -> SimulationStatus:
        return self._runtime.status

    @property
    def stats(self) -> SimulationStats:
        return self._stats

    @property
    def runtime(self) -> ContinuousRuntime:
        return self._runtime

    # --- Sink registration ---

    def add_telemetry_sink(self, sink: TelemetrySink) -> None:
        self._telemetry_sinks.append(sink)

    def add_analytics_sink(self, sink: AnalyticsSink) -> None:
        self._analytics_sinks.append(sink)

    def add_event_sink(self, sink: EventSink) -> None:
        self._event_sinks.append(sink)

    def add_live_update_sink(self, sink: LiveUpdateSink) -> None:
        self._live_update_sinks.append(sink)

    # --- Vehicle management ---

    def create_and_register_vehicle(
        self,
        vehicle_id: str,
        manufacturer: str = "Ford",
        model: str = "Transit",
        year: int = 2022,
        fuel_type: FuelType = FuelType.DIESEL,
        transmission: TransmissionType = TransmissionType.AUTOMATIC,
    ) -> Vehicle:
        """Create a vehicle entity and register it with the runtime.

        Returns:
            The created Vehicle entity.
        """
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin=f"VIN{abs(hash(vehicle_id)) % 10**10:010d}",
            specification=VehicleSpecification(
                manufacturer=manufacturer,
                model=model,
                year=year,
                fuel_type=fuel_type,
                transmission=transmission,
            ),
            status=VehicleStatus.AVAILABLE,
        )
        self._runtime.add_vehicle(vehicle)
        return vehicle

    def register_vehicle(self, vehicle: Vehicle) -> None:
        """Register an existing Vehicle entity with the runtime."""
        self._runtime.add_vehicle(vehicle)

    # --- Lifecycle ---

    def start(self) -> None:
        """Start the simulation.

        Sets up signal handlers for graceful Ctrl+C shutdown.
        """
        self._runtime.start()
        self._running = True
        self._stop_requested = False
        self._stats = SimulationStats(start_wall_time=time.perf_counter())
        self._stop_event.clear()

        # Install signal handlers for graceful shutdown
        self._original_sigint = signal.getsignal(signal.SIGINT)
        self._original_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._print_header()

    def stop(self) -> None:
        """Stop the simulation gracefully."""
        self._stop_requested = True
        self._stop_event.wait(timeout=10.0)
        self._print_summary()

    def _handle_signal(self, signum, frame):
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        print("\n\nShutdown requested...")
        self._stop_requested = True

    # --- Execution ---

    def run(self) -> None:
        """Execute the simulation loop.

        Runs continuously until stop() is called, num_ticks is reached,
        or Ctrl+C is pressed.
        """
        if self._runtime.status != SimulationStatus.RUNNING:
            raise RuntimeError("Simulation not started. Call start() first.")

        num_ticks = self._config.num_ticks
        real_time = self._config.real_time
        tick_count = 0

        while self._running:
            if self._stop_requested:
                break
            if num_ticks is not None and tick_count >= num_ticks:
                break

            # Execute one tick
            tick_start = time.perf_counter()
            result = self._runtime.step()
            tick_count += 1
            self._stats.ticks_completed = tick_count

            # Dispatch results to sinks
            self._dispatch_results(result)

            # Print live status
            self._print_tick_status(result)

            # Real-time pacing
            if real_time:
                elapsed = time.perf_counter() - tick_start
                remaining = max(
                    0,
                    self._config.real_time_interval - elapsed,
                )
                if remaining > 0:
                    time.sleep(remaining)

        self._running = False
        self._restore_signals()
        self._runtime.stop()
        self._stop_event.set()

    def _dispatch_results(self, result: TickResult) -> None:
        """Dispatch tick results to all registered sinks."""
        for vid, vtr in result.vehicle_results.items():
            if vtr.error:
                self._stats.errors.append(
                    (result.tick_id, vid, vtr.error)
                )
                continue

            # Telemetry
            if vtr.telemetry_packet is not None:
                for sink in self._telemetry_sinks:
                    sink.receive(vtr.telemetry_packet, vtr.physics_result)
                self._stats.telemetry_packets_generated += 1

            # Analytics
            if vtr.analytics_result is not None:
                for sink in self._analytics_sinks:
                    sink.receive(
                        vid,
                        result.tick_id,
                        result.simulation_time,
                        vtr.analytics_result,
                    )
                self._stats.analytics_executions += 1

                # Events (extracted from analytics)
                events = vtr.analytics_result.get("events", [])
                if events:
                    for sink in self._event_sinks:
                        sink.receive(
                            vid,
                            result.tick_id,
                            result.simulation_time,
                            events,
                        )
                    self._stats.events_generated += len(events)

        # Live updates
        if self._live_update_sinks:
            vehicle_updates = []
            for vid, vtr in result.vehicle_results.items():
                if vtr.error:
                    continue
                vehicle_updates.append(self._build_vehicle_update(vid, vtr))
            for sink in self._live_update_sinks:
                sink.receive(
                    result.tick_id,
                    result.simulation_time,
                    vehicle_updates,
                )

    def _build_vehicle_update(self, vehicle_id: str, vtr) -> dict:
        """Build a structured live update dict for one vehicle."""
        update: dict = {"vehicle_id": vehicle_id}

        if vtr.telemetry_packet is not None:
            update["telemetry"] = {
                "vehicle_id": vtr.telemetry_packet.vehicle_id,
                "tick_id": vtr.telemetry_packet.tick_id,
                "sequence_number": vtr.telemetry_packet.sequence_number,
                "sensor_readings": [
                    {
                        "name": r.sensor_name,
                        "value": getattr(r, "value", None),
                        "unit": r.unit,
                        "valid": r.valid,
                    }
                    for r in vtr.telemetry_packet.sensor_readings
                ],
            }

        if vtr.analytics_result is not None:
            update["analytics"] = {
                k: vtr.analytics_result[k]
                for k in (
                    "vehicle_health",
                    "fuel_efficiency",
                    "driver_behaviour",
                    "trip_performance",
                    "maintenance_queue",
                    "events",
                )
                if k in vtr.analytics_result
            }

        return update

    # --- Terminal output ---

    def _print_header(self) -> None:
        """Print simulation start header."""
        print()
        print("=" * 70)
        print("DIGITAL TWIN SIMULATION STARTED")
        print("=" * 70)
        print(f"Vehicles: {len(self._runtime.get_all_vehicles())}")
        print(f"Mode: {'REAL-TIME' if self._config.real_time else 'ACCELERATED'}")
        if self._config.num_ticks:
            print(f"Ticks: {self._config.num_ticks}")
        else:
            print("Ticks: infinite (Ctrl+C to stop)")
        print("=" * 70)
        print()

    def _print_tick_status(self, result: TickResult) -> None:
        """Print concise live status for one tick."""
        time_str = result.simulation_time.strftime("%Y-%m-%d %H:%M:%S")

        # Header
        print()
        print("=" * 70)
        print(f"TICK {result.tick_id:04d} | SIMULATION TIME {time_str}")
        print("=" * 70)

        # Per-vehicle status
        for vid, vtr in result.vehicle_results.items():
            if vtr.error:
                print(f"\n{vid}")
                print(f"  ERROR: {vtr.error}")
                continue

            # Get vehicle state from runtime
            vehicle = self._runtime.get_vehicle(vid)
            if vehicle is None:
                continue

            state = vehicle.state
            print(f"\n{vid}")
            print(f"  speed: {state.current_speed_kmh:5.1f} km/h")
            print(f"  rpm: {state.current_rpm:5.0f}")
            print(f"  fuel: {state.fuel_level_percent:5.1f}%")
            print(f"  engine_temp: {state.engine_temperature_celsius:5.1f}°C")

            # Telemetry status
            if vtr.telemetry_packet is not None:
                print(f"  telemetry: generated (seq={vtr.telemetry_packet.sequence_number})")
            else:
                print("  telemetry: failed")

            # Analytics status
            if vtr.analytics_result is not None:
                events = vtr.analytics_result.get("events", [])
                print(f"  analytics: completed (events={len(events)})")
            else:
                print("  analytics: failed")

        # Footer with stats
        print()
        print("-" * 70)
        print(
            f"  packets: {self._stats.telemetry_packets_generated} | "
            f"analytics: {self._stats.analytics_executions} | "
            f"events: {self._stats.events_generated} | "
            f"errors: {len(self._stats.errors)}"
        )
        print("-" * 70)

    def _print_summary(self) -> None:
        """Print final simulation summary."""
        elapsed = time.perf_counter() - self._stats.start_wall_time
        sim_seconds = self._stats.ticks_completed

        print()
        print("=" * 70)
        print("Simulation stopped gracefully.")
        print()
        print("Final summary:")
        print(f"  ticks completed: {self._stats.ticks_completed}")
        print(f"  simulated duration: {sim_seconds} seconds")
        print(f"  wall-clock duration: {elapsed:.1f} seconds")
        print(f"  vehicles: {len(self._runtime.get_all_vehicles())}")
        print(f"  telemetry packets generated: {self._stats.telemetry_packets_generated}")
        print(f"  analytics executions: {self._stats.analytics_executions}")
        print(f"  events generated: {self._stats.events_generated}")
        if self._stats.errors:
            print(f"  errors: {len(self._stats.errors)}")
            for tick_id, vid, err in self._stats.errors[:5]:
                print(f"    tick={tick_id} vehicle={vid}: {err}")
        print("=" * 70)
        print()

    def _restore_signals(self) -> None:
        """Restore original signal handlers."""
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)
