"""M5.2 regression test for the application lifespan shutdown.

Drives the real FastAPI lifespan (startup and teardown) with a live
runtime writing to the test database, then asserts the properties the
production incident lacked:

* teardown disposes the SQLAlchemy engine while the event loop is alive;
* no pooled connection is still checked out afterwards;
* the garbage collector is never asked to clean up a non-checked-in
  connection (the SAWarning seen on every Ctrl+C in local testing);
* the simulation run task is gone — no orphaned runtime survives
  shutdown.
"""

import asyncio
import gc
import warnings

import pytest
from sqlalchemy import text

from backend.api.main import app, lifespan
from backend.db.session import async_session_factory, close_db, engine, init_db

# The exact warning SQLAlchemy emits when a connection is torn down by the
# garbage collector instead of being returned to the pool.
_LEAK_WARNING = "non-checked-in connection"


@pytest.fixture(autouse=True)
async def _schema():
    # The shared engine may hold connections bound to a previous test's
    # closed loop (same reason as tests/integration/conftest.py), so purge
    # the pool before creating the schema.
    await close_db()
    await init_db()
    yield
    await close_db()


@pytest.fixture
def fresh_websocket_queues(monkeypatch: pytest.MonkeyPatch):
    """Rebind the module-level WebSocket queues to this event loop.

    ``snapshot_queue``/``trips_queue``/``alerts_queue`` are process-level
    singletons that bind to the first loop that awaits them. Driving the
    lifespan in several tests would otherwise fail with "Queue is bound to
    a different event loop" — a test artifact, never a server condition
    (one server = one loop). Fresh queues keep this test independent of
    the module state other tests leave behind.
    """
    from backend.api.websocket import alerts as alerts_module
    from backend.api.websocket import dashboard as dashboard_module
    from backend.api.websocket import trips as trips_module

    originals = (
        (dashboard_module, "snapshot_queue", dashboard_module.snapshot_queue),
        (trips_module, "trips_queue", trips_module.trips_queue),
        (alerts_module, "alerts_queue", alerts_module.alerts_queue),
    )
    for module, attribute, _original in originals:
        monkeypatch.setattr(module, attribute, asyncio.Queue())

    # main.py imported the queue objects directly, so rebind those too.
    import backend.api.main as main_module

    monkeypatch.setattr(
        main_module, "snapshot_queue", dashboard_module.snapshot_queue
    )
    monkeypatch.setattr(main_module, "trips_queue", trips_module.trips_queue)
    monkeypatch.setattr(main_module, "alerts_queue", alerts_module.alerts_queue)

    yield


class TestLifespanShutdown:
    """The lifespan is driven once per test with its own queue singletons:
    the module-level queues bind to the first event loop that awaits them,
    so a second start/stop cycle in the same process would otherwise fail
    with "bound to a different event loop" — an artifact of testing one
    process, never a server condition."""

    async def test_teardown_is_deterministic_and_leak_free(
        self,
        monkeypatch: pytest.MonkeyPatch,
        fresh_websocket_queues: None,
    ) -> None:
        from backend.api.main import simulation_controller

        disposed: list[bool] = []

        async def _record_dispose() -> None:
            disposed.append(True)
            await close_db()

        monkeypatch.setattr("backend.api.main.close_db", _record_dispose)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            async with lifespan(app):
                assert simulation_controller.running is True, (
                    "the default fleet must be running during startup"
                )
                run_task = simulation_controller._task
                assert run_task is not None

                # Exercise real database work while the runtime is live.
                async with async_session_factory() as session:
                    await session.execute(text("select 1"))
                await asyncio.sleep(0.05)  # let the runtime tick

            gc.collect()

        assert disposed == [True], "lifespan teardown must dispose the engine"
        assert engine.pool.checkedout() == 0, (
            "every pooled connection must be returned before shutdown ends"
        )
        assert run_task.done(), "the run task must be finished after shutdown"
        assert run_task.cancelled(), "shutdown must cancel the run task"
        assert simulation_controller.running is False
        assert simulation_controller._task is None

        leaks = [str(w.message) for w in caught if _LEAK_WARNING in str(w.message)]
        assert not leaks, (
            f"connections were garbage-collected instead of returned: {leaks}"
        )
