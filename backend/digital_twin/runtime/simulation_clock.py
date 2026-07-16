"""SimulationClock: owns simulation time and clock speed.

The clock is the single source of truth for "what time is it in the
simulation." It knows nothing about managers, ticks' business content,
or execution order -- it only advances time and tracks pause state.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from digital_twin.common.exceptions import SimulationStateError
from digital_twin.config.simulation_config import ClockConfig

logger = logging.getLogger(__name__)


class SimulationClock:
    """Owns and advances simulated time independent of wall-clock time.

    Supports accelerated time via a configurable clock speed multiplier,
    e.g. a clock_speed of 60.0 means each tick advances simulated time
    by 60x the configured base seconds-per-tick (1 real second of
    simulation stepping == 1 simulated minute).
    """

    def __init__(
        self,
        config: ClockConfig,
        start_time: datetime | None = None,
    ) -> None:
        """Initialize the clock.

        Args:
            config: Clock configuration (tick interval, base seconds
                per tick, initial clock speed).
            start_time: Simulated time to start at. Defaults to the
                current wall-clock time if not provided.
        """
        self._config = config
        self._start_time = start_time or datetime.now()
        self._current_time = self._start_time
        self._clock_speed = config.initial_clock_speed
        self._tick_id = 0
        self._is_paused = False
        self._is_running = False

    @property
    def tick_id(self) -> int:
        """int: The current tick counter, starting at 0."""
        return self._tick_id

    @property
    def current_time(self) -> datetime:
        """datetime: The current simulated time."""
        return self._current_time

    @property
    def clock_speed(self) -> float:
        """float: Current clock speed multiplier (simulated s / real s)."""
        return self._clock_speed

    @property
    def is_paused(self) -> bool:
        """bool: Whether the clock is currently paused."""
        return self._is_paused

    @property
    def is_running(self) -> bool:
        """bool: Whether the clock has been started and not stopped."""
        return self._is_running

    def set_clock_speed(self, speed: float) -> None:
        """Set the clock speed multiplier.

        Args:
            speed: New multiplier. Must be strictly positive.

        Raises:
            ValueError: If speed is not positive.
        """
        if speed <= 0:
            raise ValueError("Clock speed must be positive.")
        logger.debug("Clock speed changed from %s to %s", self._clock_speed, speed)
        self._clock_speed = speed

    def start(self) -> None:
        """Mark the clock as running.

        Raises:
            SimulationStateError: If the clock is already running.
        """
        if self._is_running:
            raise SimulationStateError("Clock is already running.")
        self._is_running = True
        self._is_paused = False
        logger.info("Simulation clock started at %s", self._current_time)

    def pause(self) -> None:
        """Pause the clock; advance() becomes a no-op until resume().

        Raises:
            SimulationStateError: If the clock is not running.
        """
        if not self._is_running:
            raise SimulationStateError("Cannot pause a clock that is not running.")
        self._is_paused = True
        logger.info("Simulation clock paused at tick %s", self._tick_id)

    def resume(self) -> None:
        """Resume a paused clock.

        Raises:
            SimulationStateError: If the clock is not currently paused.
        """
        if not self._is_paused:
            raise SimulationStateError("Cannot resume a clock that is not paused.")
        self._is_paused = False
        logger.info("Simulation clock resumed at tick %s", self._tick_id)

    def reset(self, start_time: datetime | None = None) -> None:
        """Reset the clock to its initial state.

        Args:
            start_time: New simulated start time. Defaults to the
                original start_time passed at construction.
        """
        self._current_time = start_time or self._start_time
        self._tick_id = 0
        self._clock_speed = self._config.initial_clock_speed
        self._is_paused = False
        self._is_running = False
        logger.info("Simulation clock reset to %s", self._current_time)

    def advance(self) -> float:
        """Advance simulated time by one tick, respecting clock speed.

        Returns:
            delta_time: Simulated seconds elapsed this tick. Returns 0.0
            if the clock is paused or not running.

        Raises:
            SimulationStateError: If the clock has never been started.
        """
        if not self._is_running:
            raise SimulationStateError("Cannot advance a clock that has not started.")
        if self._is_paused:
            return 0.0

        delta_time = self._config.simulated_seconds_per_tick * self._clock_speed
        self._current_time += timedelta(seconds=delta_time)
        self._tick_id += 1
        return delta_time