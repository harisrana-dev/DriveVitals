"""Simulation controller for the Digital Twin Lab.

Owns the lifecycle of the (single) live fleet simulation task. A launched
scenario reconfigures the :class:`DriveVitalsRuntime` fleet and (re)runs
its loop to completion. Only one simulation runs at a time; launching
another stops the current one first.

The controller deliberately knows nothing about HTTP, WebSockets or
clients. It is a thin, synchronous-safe wrapper around the async runtime
task lifecycle.

Lifecycle ownership (M5.2):
  * ``stop()``        — cancels a live run task AND awaits it, then drains
    tracked background persistence tasks (scenario switches).
  * ``shutdown()``    — the deterministic app-teardown path: cancel + await
    the run task, then cancel + await persistence background tasks so
    every SQLAlchemy session returns its connection to the pool before
    the engine is disposed. Cancellation is never fire-and-forget.
  * a run task that finishes *naturally* (all trips completed or the
    configured scenario duration elapsed) is reported through the
    optional ``run_finished`` callback; cancellation never triggers it.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from backend.application.runtime import DriveVitalsRuntime
from backend.fleet.config.fleet_factory import FleetConfiguration

logger = logging.getLogger(__name__)

RunFinishedCallback = Callable[[str, str], Awaitable[None]]


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
        self._run_finished_callback: RunFinishedCallback | None = None

    def set_run_finished_callback(
        self,
        callback: RunFinishedCallback | None,
    ) -> None:
        """Register an async ``callback(scenario_id, run_id)`` invoked when a
        scenario run task finishes *naturally* (all trips completed or the
        configured duration elapsed).

        Cancellation through ``stop()``/``shutdown()`` never triggers it —
        those paths own the DB lifecycle updates themselves. The coroutine
        is scheduled through the persistence service so it is tracked and
        drained/cancelled with every other background DB task.
        """
        self._run_finished_callback = callback

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

        self._task = self._spawn_run()

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
        simulation_speed: float = 1.0,
        duration_seconds: int | None = None,
    ) -> dict:
        """Launch a scenario, replacing any currently-running simulation.

        Reconfigures the runtime fleet around ``config`` then starts a
        fresh run task. The scenario's seed / simulation speed / duration
        are passed through to the runtime so they actually govern the run
        (M5.2: these fields must be functional, not decorative). Returns
        the controller status.
        """
        await self.stop()

        self._runtime.configure_fleet(config)

        self._scenario_id = scenario_id
        self._scenario_name = scenario_name
        self._run_id = run_id
        self._started_at = datetime.now(timezone.utc)
        self._vehicles = len(config.assignments)

        self._task = self._spawn_run(
            seed=seed,
            simulation_speed=simulation_speed,
            duration_seconds=duration_seconds,
        )

        logger.info(
            "Simulation launched scenario=%s run=%s vehicles=%d seed=%s "
            "speed=%sx duration=%ss",
            scenario_id,
            run_id,
            self._vehicles,
            seed,
            simulation_speed,
            duration_seconds,
        )

        return self.status()

    def _spawn_run(
        self,
        *,
        seed: int | None = None,
        simulation_speed: float = 1.0,
        duration_seconds: int | None = None,
    ) -> asyncio.Task:
        """Create the runtime run task with its per-run options and register
        the natural-completion watcher."""
        task = asyncio.create_task(
            self._runtime.run(
                seed=seed,
                simulation_speed=simulation_speed,
                duration_seconds=duration_seconds,
            )
        )
        task.add_done_callback(self._on_run_finished)
        return task

    def _on_run_finished(self, task: asyncio.Task) -> None:
        """Done-callback for a run task.

        Only a run that finished *naturally* while still owned by this
        controller is reported: cancelled tasks (stop/relaunch/shutdown)
        and superseded tasks are ignored, and exceptions are logged rather
        than finalised as a success. The callback coroutine is scheduled
        through ``schedule_background`` so shutdown drains/cancels it like
        every other DB task.
        """
        if task is not self._task:
            # stop()/launch()/shutdown() detached the task first; they own
            # the persisted lifecycle update for this run.
            return
        if task.cancelled():
            return
        error = task.exception()
        if error is not None:
            logger.error(
                "Simulation run for scenario=%s finished with an error",
                self._scenario_id,
                exc_info=error,
            )
            return
        scenario_id = self._scenario_id
        run_id = self._run_id
        callback = self._run_finished_callback
        if scenario_id is None or run_id is None or callback is None:
            return
        persistence = self._runtime.persistence_service
        if persistence is None:
            return
        persistence.schedule_background(
            callback(scenario_id, run_id)
        )
        logger.info(
            "Simulation run finished naturally scenario=%s run=%s",
            scenario_id,
            run_id,
        )

    async def stop(self) -> dict:
        """Stop the currently-running simulation, if any.

        Cancels the run task, halts the runtime loop, and drains every
        tracked background persistence task (telemetry, alerts, trip
        completion, ...) so no writer from the stopped run can keep
        mutating rows while a fresh run is being launched. In-memory
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

        persistence = self._runtime.persistence_service
        if persistence is not None:
            await persistence.drain_background_tasks()

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

    async def shutdown(self) -> None:
        """Deterministic app-teardown used from the FastAPI lifespan.

        Sequence: stop the runtime loop, cancel the run task, **await** it
        (fire-and-forget cancellation leaves in-flight SQLAlchemy work to
        be garbage-collected mid-transaction, which produced the
        "non-checked-in connection" warnings), then cancel **and await**
        every tracked background persistence task so each session has
        unwound and returned its connection to the pool before the engine
        is disposed.

        Unlike ``stop()`` (scenario switches, which drain writers
        gracefully), shutdown does not wait for straggler writes to
        complete — it bounds them deterministically instead, so a hung
        task can never wedge application teardown.

        Expected ``asyncio.CancelledError`` from the cancelled run task is
        handled here and never re-raised as an application error.
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
                    "Simulation task raised during shutdown for scenario=%s",
                    self._scenario_id,
                )

        persistence = self._runtime.persistence_service
        if persistence is not None:
            await persistence.cancel_and_wait_background_tasks()

        logger.info("Simulation controller shut down")

