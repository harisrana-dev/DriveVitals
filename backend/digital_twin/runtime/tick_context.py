"""Defines TickContext, the immutable object passed to every module on tick.

TickContext is intentionally a plain, frozen dataclass with no behavior.
It is a data-transfer object: the Scheduler builds one per tick from the
SimulationClock, and every manager receives the same instance for that
tick so all modules observe a single consistent view of "now".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from digital_twin.common.enums import SimulationStatus


@dataclass(frozen=True)
class TickContext:
    """Immutable snapshot of simulation state for a single tick.

    Attributes:
        tick_id: Monotonically increasing tick counter, starting at 0.
        simulation_time: Current simulated wall-clock time.
        delta_time: Simulated seconds elapsed since the previous tick.
        clock_speed: Current clock speed multiplier (simulated
            seconds per real second).
        random_seed: Seed to use for any variation-only randomness
            during this tick, so runs are reproducible.
        simulation_state: Current lifecycle state of the simulation
            (RUNNING, PAUSED, STOPPED).
        metadata: Optional read-only bag of additional per-tick data
            that future sprints (e.g. environment events) may attach
            without changing this dataclass's shape.
    """

    tick_id: int
    simulation_time: datetime
    delta_time: float
    clock_speed: float
    random_seed: int
    simulation_state: SimulationStatus
    metadata: Mapping[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """Normalize optional fields.

        Ensures `metadata` is always a mapping, never None, so
        consumers can do `context.metadata.get(...)` unconditionally.
        """
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    def with_metadata(self, **updates: Any) -> "TickContext":
        """Return a new TickContext with additional metadata merged in.

        Since TickContext is frozen, this is the supported way for a
        module earlier in execution order to pass extra data forward
        to modules later in the same tick (e.g. Environment attaching
        a weather event that Dispatch reads later in the same tick).

        Args:
            **updates: Key/value pairs to merge into `metadata`.

        Returns:
            A new TickContext instance with merged metadata; all other
            fields are copied unchanged.
        """
        merged = dict(self.metadata)
        merged.update(updates)
        return TickContext(
            tick_id=self.tick_id,
            simulation_time=self.simulation_time,
            delta_time=self.delta_time,
            clock_speed=self.clock_speed,
            random_seed=self.random_seed,
            simulation_state=self.simulation_state,
            metadata=merged,
        )