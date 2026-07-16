"""Scheduler: enforces the fixed per-tick execution order.

The Digital Twin's execution order is a frozen architectural decision:

    Environment -> Dispatch -> Drivers -> Vehicles -> Trips -> Maintenance

(Clock is advanced separately, upstream, by the runtime before the
scheduler runs -- see DigitalTwinRuntime.) The Scheduler's only
responsibility is coordinating *when* each registered manager runs. It
contains no business logic of its own.
"""

from __future__ import annotations

import logging
from typing import Iterable

from digital_twin.common.enums import ExecutionPhase
from digital_twin.common.exceptions import ConfigurationError
from digital_twin.common.interfaces import TickableManager
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)

#: Fixed, frozen execution order. Do not reorder.
_PHASE_ORDER: tuple[ExecutionPhase, ...] = (
    ExecutionPhase.ENVIRONMENT,
    ExecutionPhase.DISPATCH,
    ExecutionPhase.DRIVERS,
    ExecutionPhase.VEHICLES,
    ExecutionPhase.TRIPS,
    ExecutionPhase.MAINTENANCE,
)


class Scheduler:
    """Coordinates execution order of managers across a single tick.

    Managers are registered against a fixed set of execution phases.
    On each tick, the Scheduler invokes `on_tick` for every manager
    registered to a phase, in phase order, then in registration order
    within a phase.
    """

    def __init__(self) -> None:
        """Initialize an empty scheduler with no registered managers."""
        self._managers_by_phase: dict[ExecutionPhase, list[TickableManager]] = {
            phase: [] for phase in _PHASE_ORDER
        }

    def register(self, manager: TickableManager) -> None:
        """Register a manager to run during its declared phase.

        Args:
            manager: A manager implementing the TickableManager
                protocol (exposes `.phase` and `.on_tick`).

        Raises:
            ConfigurationError: If the manager declares a phase outside
                the fixed, known execution order.
        """
        if manager.phase not in self._managers_by_phase:
            raise ConfigurationError(
                f"Unknown execution phase '{manager.phase}' for manager "
                f"'{type(manager).__name__}'."
            )
        self._managers_by_phase[manager.phase].append(manager)
        logger.debug(
            "Registered %s in phase %s", type(manager).__name__, manager.phase.name
        )

    def registered_managers(self) -> Iterable[TickableManager]:
        """Yield all registered managers in fixed execution order.

        Returns:
            An iterable of managers ordered by phase, then by
            registration order within each phase.
        """
        for phase in _PHASE_ORDER:
            yield from self._managers_by_phase[phase]

    def run_tick(self, context: TickContext) -> None:
        """Run one full tick across all registered managers, in order.

        Args:
            context: The immutable TickContext for this tick, built by
                the DigitalTwinRuntime from the current clock state.
        """
        for phase in _PHASE_ORDER:
            for manager in self._managers_by_phase[phase]:
                logger.debug(
                    "tick=%s phase=%s manager=%s",
                    context.tick_id,
                    phase.name,
                    type(manager).__name__,
                )
                manager.on_tick(context)