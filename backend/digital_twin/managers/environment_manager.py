"""EnvironmentManager: owns weather, traffic, road conditions, and road events.

Per Digital Twin principle #3 (Reality over randomness), randomness
here only introduces *variation* in environmental conditions -- it
never directly drives vehicle/driver behavior. Downstream managers
(Dispatch, Drivers, Vehicles) read the environment state via
TickContext metadata and decide how to react to it.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from digital_twin.common.enums import (
    ExecutionPhase,
    RoadCondition,
    WeatherCondition,
)
from digital_twin.config.simulation_config import EnvironmentManagerConfig
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


@dataclass
class RoadEvent:
    """A discrete road event affecting a region (construction, accident, etc.).

    Attributes:
        event_id: Unique identifier for the event.
        condition: The RoadCondition this event represents.
        location: Free-form location label/region affected.
        started_at_tick: Tick id at which the event began.
        duration_ticks: How many ticks the event lasts.
    """

    event_id: str
    condition: RoadCondition
    location: str
    started_at_tick: int
    duration_ticks: int


@dataclass
class EnvironmentState:
    """Current snapshot of environmental conditions.

    Attributes:
        weather: Current weather condition, fleet-wide.
        road_condition: Current dominant road condition, fleet-wide.
        active_events: Currently active RoadEvent instances.
    """

    weather: WeatherCondition = WeatherCondition.CLEAR
    road_condition: RoadCondition = RoadCondition.NORMAL
    active_events: list[RoadEvent] = field(default_factory=list)


class EnvironmentManager:
    """Owns fleet-wide environmental conditions and road events.

    Sprint 1 models environment at a single fleet-wide granularity
    (not per-region/per-route); regional environment modeling is left
    as a future extension point, since it depends on route/geography
    data owned by future Entities.
    """

    def __init__(self, config: EnvironmentManagerConfig) -> None:
        """Initialize the environment at its configured default state.

        Args:
            config: Default weather and random seed configuration.
        """
        self._config = config
        self._rng = random.Random(config.random_seed)
        self._state = EnvironmentState(weather=WeatherCondition(config.default_weather))
        self._next_event_id = 0

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: EnvironmentManager runs during the ENVIRONMENT phase."""
        return ExecutionPhase.ENVIRONMENT

    @property
    def state(self) -> EnvironmentState:
        """EnvironmentState: The current environment snapshot."""
        return self._state

    def set_weather(self, weather: WeatherCondition) -> None:
        """Explicitly set the current weather condition.

        Args:
            weather: New weather condition to apply fleet-wide.
        """
        logger.info("Weather changed %s -> %s", self._state.weather, weather)
        self._state.weather = weather

    def set_road_condition(self, condition: RoadCondition) -> None:
        """Explicitly set the current dominant road condition.

        Args:
            condition: New road condition to apply fleet-wide.
        """
        logger.info("Road condition changed %s -> %s", self._state.road_condition, condition)
        self._state.road_condition = condition

    def add_road_event(
        self,
        condition: RoadCondition,
        location: str,
        current_tick: int,
        duration_ticks: int,
    ) -> RoadEvent:
        """Add a discrete road event (construction, accident, etc.).

        Args:
            condition: RoadCondition this event represents.
            location: Free-form location label/region affected.
            current_tick: Tick id at which this event starts.
            duration_ticks: How many ticks the event should last.

        Returns:
            The newly created RoadEvent.
        """
        event = RoadEvent(
            event_id=f"event-{self._next_event_id}",
            condition=condition,
            location=location,
            started_at_tick=current_tick,
            duration_ticks=duration_ticks,
        )
        self._next_event_id += 1
        self._state.active_events.append(event)
        logger.info("Road event added: %s at %s (%s)", condition.value, location, event.event_id)
        return event

    def list_active_events(self) -> list[RoadEvent]:
        """List currently active road events.

        Returns:
            All RoadEvent instances not yet expired.
        """
        return list(self._state.active_events)

    def _expire_events(self, current_tick: int) -> None:
        """Remove road events whose duration has elapsed.

        Args:
            current_tick: The current tick id.
        """
        still_active = [
            e
            for e in self._state.active_events
            if current_tick < e.started_at_tick + e.duration_ticks
        ]
        expired = [e for e in self._state.active_events if e not in still_active]
        for event in expired:
            logger.info("Road event expired: %s", event.event_id)
        self._state.active_events = still_active

    def on_tick(self, context: TickContext) -> None:
        """Advance environment state and expire finished road events.

        Sprint 1 does not introduce autonomous weather transitions
        (that belongs to a future weather-model extension); this hook
        currently only expires timed-out road events. EnvironmentManager
        runs first in the fixed execution order, so any manager that
        needs the current environment this tick should take an
        `EnvironmentManager` (or a narrower read-only view of it) as a
        constructor dependency and read `.state` directly, rather than
        relying on TickContext propagation -- the Scheduler in Sprint 1
        dispatches the same immutable TickContext to every manager and
        does not chain per-manager mutations through it.

        Args:
            context: The current tick's immutable context.
        """
        self._expire_events(context.tick_id)
        logger.debug(
            "EnvironmentManager on_tick tick_id=%s weather=%s road=%s active_events=%d",
            context.tick_id,
            self._state.weather.value,
            self._state.road_condition.value,
            len(self._state.active_events),
        )