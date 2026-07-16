"""Manager interfaces (Protocols) shared by the runtime, scheduler, and managers.

The runtime and scheduler depend only on these Protocols, never on
concrete manager classes. This satisfies the architectural requirement
that "Runtime must not know implementation details of managers" and
that "Managers must communicate through interfaces rather than direct
coupling wherever practical."
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from digital_twin.common.enums import ExecutionPhase
from digital_twin.runtime.tick_context import TickContext


@runtime_checkable
class TickableManager(Protocol):
    """Protocol for any manager that participates in the tick loop.

    Every manager registered with the Scheduler must implement `phase`
    (which fixed execution phase it belongs to) and `on_tick` (its
    per-tick update hook). Managers contain no cross-phase ordering
    logic themselves; the Scheduler is solely responsible for ordering.
    """

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: The fixed phase this manager executes in."""
        ...

    def on_tick(self, context: TickContext) -> None:
        """Perform this manager's per-tick update.

        Args:
            context: Immutable snapshot of simulation state for the
                current tick.
        """
        ...