"""Simulation controller for the Digital Twin Lab.

Owns the lifecycle of the (single) live fleet simulation task. A launched
scenario reconfigures the :class:`DriveVitalsRuntime` fleet and (re)runs
its loop to completion. Only one simulation runs at a time; launching
another stops the current one first.

The controller deliberately knows nothing about HTTP, WebSockets or
clients. It is a thin, synchronous-safe wrapper around the async runtime
task lifecycle.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.config.fleet_factory import FleetConfiguration

logger = logging.getLogger(__name__)


class SimulationController:
    def __init__(
        self,
        runtime: DriveVitalsRuntime,
    ) -> None:
        self._runtime = runtime
        self._task: asyncio.Task | None = None
        self._scenario_id: str | None = None
        self._scenario_name: str | None = None
        self._run_id: str | None = None
        self._started_at: datetime | None = None
        self._vehicles = 0

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def scenario_id(self) -> str | None:
        return self._scenario_id

    @property
    def scenario_name(self) -> str | None:
        return self._scenario_name

    @property
    def run_id(self) -> str | None:
        return self._run_id

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def vehicles(self) -> int:
        return self._vehicles

    def status(self) -> dict:
        return {
            "running": self.running,
            "scenario_id": self._scenario_id,
            "scenario_name": self._scenario_name,
            "run_id": self._run_id,
            "started_at": self._started_at,
            "vehicles": self._vehicles,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start_default(self, run_id: str | None = None) -> dict:
        """Start the default (factory-derived) fleet, preserving the
        existing auto-start behavior. No scenario identity is attached."""
        await self.stop()

        self._scenario_id = None
        self._scenario_name = None
        self._run_id = run_id
        self._started_at = datetime.now(timezone.utc)
        self._vehicles = len(self._runtime.fleet._runners)

        self._task = asyncio.create_task(self._runtime.run())

        logger.info(
            "Default fleet simulation started run=%s vehicles=%d",
            run_id,
            self._vehicles,
        )

        return self.status()

    async def launch(
        self,
        config: FleetConfiguration,
        *,
        scenario_id: str,
        scenario_name: str,
        run_id: str,
        seed: int | None = None,
    ) -> dict:
        """Launch a scenario, replacing any currently-running simulation.

        Reconfigures the runtime fleet around ``config`` then starts a
        fresh run task. Returns the controller status.
        """
        await self.stop()

        self._runtime.configure_fleet(config)

        self._scenario_id = scenario_id
        self._scenario_name = scenario_name
        self._run_id = run_id
        self._started_at = datetime.now(timezone.utc)
        self._vehicles = len(config.assignments)

        self._task = asyncio.create_task(
            self._runtime.run()
        )

        logger.info(
            "Simulation launched scenario=%s run=%s vehicles=%d seed=%s",
            scenario_id,
            run_id,
            self._vehicles,
            seed,
        )

        return self.status()

    async def stop(self) -> dict:
        """Stop the currently-running simulation, if any.

        Cancels the run task and halts the runtime loop. In-memory
        analytics are preserved; stale in-progress trips are aborted by
        the next launch or by an explicit reset.
        """
        task = self._task
        self._task = None

        if task is not None and not task.done():
            self._runtime.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Simulation task raised during stop for scenario=%s",
                    self._scenario_id,
                )

        self._scenario_id = None
        self._scenario_name = None
        self._run_id = None
        self._started_at = None
        self._vehicles = 0

        logger.info("Simulation stopped")

        return self.status()

    async def reset(self) -> dict:
        """Fully reset: stop any run and restore the default fleet.

        In-memory analytics are cleared (via ``reset_fleet``) so the next
        launch starts from a clean slate.
        """
        await self.stop()
        self._runtime.reset_fleet()
        logger.info("Simulation reset to default fleet")
        return self.status()

    def shutdown(self) -> None:
        """Best-effort synchronous stop used from the app teardown."""
        if self._task is not None and not self._task.done():
            self._runtime.stop()
            self._task.cancel()
