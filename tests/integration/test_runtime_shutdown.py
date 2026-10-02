"""M5.2 regression tests for deterministic runtime shutdown.

The reported production symptom was:

    DriveVitals runtime stopped
    INFO: Application shutdown complete.
    INFO: Finished server process
    ...
    SAWarning: The garbage collector is trying to clean up
    non-checked-in connection <AdaptedConnection ...>

Root cause: application-owned background work was cancelled but never
awaited (``task.cancel()`` with no subsequent await, and a synchronous
``shutdown()`` that could not await at all), and the SQLAlchemy engine was
never disposed while the event loop was still alive. The run task and the
tracked persistence tasks could therefore still hold checked-out
connections when the loop closed, leaving the garbage collector to tear
them down.

These tests pin the corrected contract:

* ``shutdown()`` awaits the cancelled run task;
* ``shutdown()`` cancels *and awaits* tracked persistence tasks, so each
  connection is returned to the pool;
* the engine reports zero checked-out connections afterwards;
* cancellation surfaces as ``CancelledError`` handling, not application
  errors;
* scenario parameters (seed/speed/duration) reach the runtime, and a
  naturally finished run is reported exactly once while a cancelled run
  is not.
"""

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from backend.application.simulation_controller import SimulationController
from backend.db.persistence_service import PersistenceService
from backend.db.session import async_session_factory, engine, init_db
from backend.fleet.config.fleet_factory import FleetConfiguration
from backend.fleet.models.assignment import Assignment
from backend.fleet.models.driver import Driver
from backend.fleet.models.route import Route
from backend.fleet.models.vehicle import Vehicle


class _StubFleet:
    def __init__(self) -> None:
        self._runners: list = []


class _StubRuntime:
    """Minimal runtime facade: records run() options and never touches a DB."""

    def __init__(
        self,
        run_impl=None,
        persistence: PersistenceService | None = None,
    ) -> None:
        self.fleet = _StubFleet()
        self.stopped = False
        self.run_calls: list[dict] = []
        self._persistence = persistence
        self._run_impl = run_impl or self._never_finishes

    @property
    def persistence_service(self) -> PersistenceService | None:
        return self._persistence

    def stop(self) -> None:
        self.stopped = True

    def configure_fleet(self, config: FleetConfiguration) -> None:
        self.fleet = _StubFleet()

    async def run(self, **options) -> None:
        self.run_calls.append(options)
        await self._run_impl()

    @staticmethod
    async def _never_finishes() -> None:
        await asyncio.sleep(3600)


def _config() -> FleetConfiguration:
    vehicle = Vehicle(vehicle_id="cv-1", make="Ford", model="Transit", year=2024)
    driver = Driver(driver_id="cd-1", name="Test Driver", behavior_profile="eco")
    route = Route(
        route_id="cr-1",
        origin="A",
        destination="B",
        distance_km=1.0,
        route_type="urban",
        speed_limit_kmh=50.0,
    )
    assignment = Assignment(
        assignment_id="ca-1",
        driver_id="cd-1",
        vehicle_id="cv-1",
        route_id="cr-1",
    )
    return FleetConfiguration(
        vehicles=[vehicle],
        drivers=[driver],
        routes=[route],
        assignments=[assignment],
    )


class TestShutdownAwaitsCancelledWork:
    async def test_shutdown_awaits_the_run_task(self) -> None:
        started = asyncio.Event()

        async def _run() -> None:
            started.set()
            await asyncio.sleep(3600)

        runtime = _StubRuntime(_run)
        controller = SimulationController(runtime)
        await controller.start_default(run_id="r1")
        await started.wait()

        run_task = controller._task
        await controller.shutdown()

        assert run_task.done(), "run task must be awaited by shutdown"
        assert run_task.cancelled()
        assert runtime.stopped, "runtime loop must be stopped before cancel"
        assert controller.running is False

    async def test_shutdown_is_idempotent_without_a_run(self) -> None:
        runtime = _StubRuntime()
        controller = SimulationController(runtime)

        await controller.shutdown()
        await controller.shutdown()

        assert controller.running is False

    async def test_shutdown_handles_task_exception_as_expected_cancellation(
        self,
    ) -> None:
        """A task that raises while being cancelled must not escape as an
        application error."""

        async def _run() -> None:
            try:
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                raise

        runtime = _StubRuntime(_run)
        controller = SimulationController(runtime)
        await controller.start_default()
        await asyncio.sleep(0)

        await controller.shutdown()  # must not raise
        assert controller.running is False



class TestShutdownReturnsConnectionsToThePool:
    """The exact failure mode: connections must be returned, not GC'd."""

    async def test_background_session_task_is_cancelled_and_awaited(self) -> None:
        await init_db()
        service = PersistenceService()
        checked_out = asyncio.Event()

        async def _holder() -> None:
            async with async_session_factory() as session:
                # Hold a real pooled connection while "blocked" on work.
                await session.execute(text("select 1"))
                checked_out.set()
                await asyncio.sleep(3600)

        task = service.schedule_background(_holder())
        await checked_out.wait()
        assert engine.pool.checkedout() == 1

        controller = SimulationController(_StubRuntime(persistence=service))
        await controller.shutdown()

        assert task.done(), "cancelled persistence task must be awaited"
        assert task.cancelled()
        assert service._background_tasks == set()
        assert engine.pool.checkedout() == 0, (
            "shutdown must return every pooled connection before the engine "
            "is disposed, otherwise the garbage collector tears them down"
        )

    async def test_straggler_task_cannot_wedge_shutdown(self) -> None:
        """A task that never completes must be bounded, not awaited forever."""
        service = PersistenceService()

        async def _stuck() -> None:
            await asyncio.sleep(3600)

        task = service.schedule_background(_stuck())
        controller = SimulationController(_StubRuntime(persistence=service))

        await asyncio.wait_for(controller.shutdown(), timeout=5.0)

        assert task.cancelled()
        assert service._background_tasks == set()


class TestRunCompletionReporting:
    async def test_scenario_parameters_reach_the_runtime(self) -> None:
        async def _returns_immediately() -> None:
            return None

        runtime = _StubRuntime(_returns_immediately)
        controller = SimulationController(runtime)

        await controller.launch(
            _config(),
            scenario_id="s1",
            scenario_name="S1",
            run_id="r1",
            seed=4242,
            simulation_speed=4.0,
            duration_seconds=600,
        )
        await asyncio.wait_for(controller._task, timeout=5.0)

        assert runtime.run_calls[-1] == {
            "seed": 4242,
            "simulation_speed": 4.0,
            "duration_seconds": 600,
        }
        await controller.stop()

    async def test_default_run_uses_neutral_options(self) -> None:
        async def _returns_immediately() -> None:
            return None

        runtime = _StubRuntime(_returns_immediately)
        controller = SimulationController(runtime)

        await controller.start_default(run_id="r1")
        await asyncio.wait_for(controller._task, timeout=5.0)

        assert runtime.run_calls[-1] == {
            "seed": None,
            "simulation_speed": 1.0,
            "duration_seconds": None,
        }
        await controller.stop()

    async def test_natural_completion_is_reported_once(self) -> None:
        service = PersistenceService()
        reported: list[tuple[str, str]] = []

        async def _callback(scenario_id: str, run_id: str) -> None:
            reported.append((scenario_id, run_id))

        async def _returns_immediately() -> None:
            return None

        runtime = _StubRuntime(_returns_immediately, persistence=service)
        controller = SimulationController(runtime)
        controller.set_run_finished_callback(_callback)

        await controller.launch(
            _config(),
            scenario_id="s1",
            scenario_name="S1",
            run_id="r1",
        )
        await asyncio.wait_for(controller._task, timeout=5.0)
        await asyncio.sleep(0)  # let the done-callback fire
        await service.drain_background_tasks()

        assert reported == [("s1", "r1")]
        assert controller.running is False

    async def test_cancelled_run_is_not_reported_as_completed(self) -> None:
        service = PersistenceService()
        reported: list[tuple[str, str]] = []

        async def _callback(scenario_id: str, run_id: str) -> None:
            reported.append((scenario_id, run_id))

        runtime = _StubRuntime(persistence=service)
        controller = SimulationController(runtime)
        controller.set_run_finished_callback(_callback)

        await controller.launch(
            _config(),
            scenario_id="s1",
            scenario_name="S1",
            run_id="r1",
        )
        await asyncio.sleep(0)  # let the run start before cancelling it
        await controller.stop()
        await asyncio.sleep(0)
        await service.drain_background_tasks()

        assert reported == [], "a stopped run must not be finalised as completed"

    async def test_failed_run_is_not_reported_as_completed(self) -> None:
        service = PersistenceService()
        reported: list[tuple[str, str]] = []

        async def _callback(scenario_id: str, run_id: str) -> None:
            reported.append((scenario_id, run_id))

        async def _explodes() -> None:
            raise RuntimeError("run failed")

        runtime = _StubRuntime(_explodes, persistence=service)
        controller = SimulationController(runtime)
        controller.set_run_finished_callback(_callback)

        await controller.launch(
            _config(),
            scenario_id="s1",
            scenario_name="S1",
            run_id="r1",
        )
        with pytest.raises(RuntimeError):
            await asyncio.wait_for(controller._task, timeout=5.0)
        await asyncio.sleep(0)
        await service.drain_background_tasks()

        assert reported == [], "a failed run must not be finalised as completed"
