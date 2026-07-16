"""DigitalTwinRuntime: top-level orchestrator of the Digital Twin simulation.

The runtime owns the SimulationClock, the Scheduler (module registry +
execution order), and the overall simulation lifecycle (start / pause /
resume / stop / reset). It contains no business logic of its own -- all
domain behavior lives in managers. The runtime's job is purely to:

    1. Advance the clock.
    2. Build a TickContext from the clock's new state.
    3. Hand that TickContext to the Scheduler to run one tick.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from digital_twin.common.enums import SimulationStatus
from digital_twin.common.exceptions import SimulationStateError
from digital_twin.config.simulation_config import SimulationConfig
from digital_twin.common.interfaces import TickableManager
from digital_twin.runtime.scheduler import Scheduler
from digital_twin.runtime.simulation_clock import SimulationClock
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class DigitalTwinRuntime:
    """Owns the simulation clock, module registry, and tick loop.

    Attributes are intentionally private; all interaction happens
    through the public lifecycle and registration methods below.
    """

    def __init__(
        self,
        config: SimulationConfig,
        clock: SimulationClock | None = None,
        scheduler: Scheduler | None = None,
    ) -> None:
        """Initialize the runtime.

        Args:
            config: Top-level simulation configuration, injected.
            clock: Optional pre-built SimulationClock. If omitted, one
                is constructed from `config.clock`. Accepting it as a
                parameter keeps the runtime testable (a test can inject
                a fake/mock clock).
            scheduler: Optional pre-built Scheduler. If omitted, an
                empty one is constructed.
        """
        self._config = config
        self._clock = clock or SimulationClock(config.clock)
        self._scheduler = scheduler or Scheduler()
        self._status = SimulationStatus.STOPPED

    @property
    def status(self) -> SimulationStatus:
        """SimulationStatus: Current lifecycle state of the simulation."""
        return self._status

    @property
    def clock(self) -> SimulationClock:
        """SimulationClock: The runtime's simulation clock."""
        return self._clock

    @property
    def config(self) -> SimulationConfig:
        """SimulationConfig: The configuration this runtime was built with."""
        return self._config

    def register_manager(self, manager: TickableManager) -> None:
        """Register a manager with the scheduler's module registry.

        Args:
            manager: A manager implementing the TickableManager
                protocol.
        """
        self._scheduler.register(manager)
        logger.info("Registered manager: %s", type(manager).__name__)

    def start(self) -> None:
        """Start the simulation.

        Raises:
            SimulationStateError: If the simulation is already running.
        """
        if self._status == SimulationStatus.RUNNING:
            raise SimulationStateError("Simulation is already running.")
        self._clock.start()
        self._status = SimulationStatus.RUNNING
        logger.info("DigitalTwinRuntime started.")

    def pause(self) -> None:
        """Pause the simulation.

        Raises:
            SimulationStateError: If the simulation is not running.
        """
        if self._status != SimulationStatus.RUNNING:
            raise SimulationStateError("Cannot pause: simulation is not running.")
        self._clock.pause()
        self._status = SimulationStatus.PAUSED
        logger.info("DigitalTwinRuntime paused.")

    def resume(self) -> None:
        """Resume a paused simulation.

        Raises:
            SimulationStateError: If the simulation is not paused.
        """
        if self._status != SimulationStatus.PAUSED:
            raise SimulationStateError("Cannot resume: simulation is not paused.")
        self._clock.resume()
        self._status = SimulationStatus.RUNNING
        logger.info("DigitalTwinRuntime resumed.")

    def stop(self) -> None:
        """Stop the simulation. A stopped runtime must be reset before restart."""
        self._status = SimulationStatus.STOPPED
        logger.info("DigitalTwinRuntime stopped.")

    def reset(self, start_time: datetime | None = None) -> None:
        """Reset the simulation clock and lifecycle state to their initial values.

        Args:
            start_time: Optional new simulated start time.
        """
        self._clock.reset(start_time=start_time)
        self._status = SimulationStatus.STOPPED
        logger.info("DigitalTwinRuntime reset.")

    def run_tick(self) -> TickContext:
        """Advance the clock by one tick and run all registered managers.

        Returns:
            The TickContext that was constructed and dispatched for
            this tick, useful for logging/testing.

        Raises:
            SimulationStateError: If the simulation is not running.
        """
        if self._status != SimulationStatus.RUNNING:
            raise SimulationStateError("Cannot tick: simulation is not running.")

        delta_time = self._clock.advance()
        context = TickContext(
            tick_id=self._clock.tick_id,
            simulation_time=self._clock.current_time,
            delta_time=delta_time,
            clock_speed=self._clock.clock_speed,
            random_seed=self._config.environment.random_seed + self._clock.tick_id,
            simulation_state=self._status,
        )
        self._scheduler.run_tick(context)
        return context

    def run_for(self, num_ticks: int, real_time_delay: bool = False) -> None:
        """Run the simulation for a fixed number of ticks.

        Args:
            num_ticks: Number of ticks to execute.
            real_time_delay: If True, sleep `config.clock.tick_interval_seconds`
                between ticks to simulate real-time pacing (useful for
                demos / manual observation). If False (default), ticks
                run back-to-back as fast as possible (useful for tests
                and batch/offline simulation).

        Raises:
            SimulationStateError: If the simulation is not running.
            ValueError: If num_ticks is negative.
        """
        if num_ticks < 0:
            raise ValueError("num_ticks must be non-negative.")

        for _ in range(num_ticks):
            self.run_tick()
            if real_time_delay:
                time.sleep(self._config.clock.tick_interval_seconds)