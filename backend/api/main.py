import asyncio
import os

from contextlib import asynccontextmanager

from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    FastAPI,
)

from sqlalchemy import update as sa_update

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.application.runtime import (
    DriveVitalsRuntime,
)

from backend.api.websocket.dashboard import (
    router as dashboard_router,
    snapshot_queue,
    snapshot_worker,
)

from backend.api.websocket.trips import (
    router as trips_router,
    trips_queue,
    trips_worker,
)

from backend.api.websocket.alerts import (
    router as alerts_router,
    alerts_queue,
    alerts_worker,
)

from backend.api.v1 import (
    api_router,
)

from backend.api.websocket.snapshot_publisher import (
    DashboardSnapshotPublisher,
)

from backend.api.simulation_state import (
    init_simulation_controller,
    simulation_controller,
)

from backend.api.websocket.trip_publisher import (
    TripSnapshotPublisher,
)

from backend.api.v1.services.admin_bootstrap import (
    AdminBootstrapConfigError,
    bootstrap_admin,
)

from backend.api.v1.services.digital_twin_service import (
    DigitalTwinService,
)

from backend.db.repositories import (
    AssignmentRepository,
    DriverRepository,
    RouteRepository,
    ScenarioRepository,
    VehicleRepository,
)

from backend.db.models.scenario import (
    SimulationRun,
    SimulationScenario,
)

from backend.db.persistence_service import (
    PersistenceService,
)

from backend.db.session import (
    async_session_factory,
    close_db,
)

from backend.trips.store.trip_store import (
    TripStore,
)

from backend.trips.services.trip_builder import (
    TripBuilder,
)

persistence_service = PersistenceService()

runtime = (
    DriveVitalsRuntime(
        persistence_service=persistence_service
    )
)

simulation_controller = init_simulation_controller(runtime)


async def _finalize_completed_run(
    scenario_id: str,
    run_id: str,
) -> None:
    """Mark a scenario run that finished naturally as completed.

    Invoked by :class:`SimulationController` (via ``schedule_background``,
    so it is tracked and drained like every other DB task) when a run task
    ends without cancellation — all trips completed or the configured
    ``duration_seconds`` elapsed. Both updates are guarded on the current
    ``running`` status so a concurrent manual stop/shutdown can never be
    overwritten by this callback.
    """
    try:
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)
            run_result = await session.execute(
                sa_update(SimulationRun)
                .where(
                    SimulationRun.run_id == run_id,
                    SimulationRun.status == "running",
                )
                .values(status="completed", end_time=now)
            )
            if run_result.rowcount:
                await session.execute(
                    sa_update(SimulationScenario)
                    .where(
                        SimulationScenario.scenario_id == scenario_id,
                        SimulationScenario.status == "running",
                    )
                    .values(status="completed")
                )
            await session.commit()
    except Exception:
        # Best-effort: the run/scenario rows are reconciled by
        # complete_active_runs() at shutdown if this fails.
        print(
            f"Failed to finalize completed run {run_id} "
            f"for scenario {scenario_id}"
        )


simulation_controller.set_run_finished_callback(
    _finalize_completed_run
)

snapshot_publisher = DashboardSnapshotPublisher(
    queue=snapshot_queue,
    builder=runtime.dashboard_builder,
)

trip_store = TripStore()

trip_builder = TripBuilder()

trip_publisher = TripSnapshotPublisher(
    queue=trips_queue,
    builder=trip_builder,
    store=trip_store,
)

snapshot_worker_task: asyncio.Task | None = None

trips_worker_task: asyncio.Task | None = None

alerts_worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    global snapshot_worker_task
    global trips_worker_task
    global alerts_worker_task

    # --------------------------------------------------------------
    # Provision the first administrator when bootstrapping a fresh
    # deployment. Idempotent (no-op once any user exists) and
    # conservative: it never promotes or alters existing users.
    # --------------------------------------------------------------

    try:
        async with async_session_factory() as session:
            result = await bootstrap_admin(session)
        if result.created and result.email:
            print(
                f"Bootstrap admin created: {result.email}"
            )
    except AdminBootstrapConfigError as exc:
        print(
            "Admin bootstrap configuration error: "
            f"{exc}"
        )
        raise

    # --------------------------------------------------------------
    # Wire persistence alert events to the alerts WebSocket queue
    # --------------------------------------------------------------

    persistence_service.set_alert_event_callback(
        alerts_queue.put_nowait
    )

    # --------------------------------------------------------------
    # Connect analytics snapshot stream to dashboard queue
    # --------------------------------------------------------------

    runtime.snapshot_stream.subscribe(
        snapshot_publisher
    )

    # --------------------------------------------------------------
    # Register trip flush callback
    # --------------------------------------------------------------

    def _dashboard_trip_completed(
        summary,
        context,
        runtime_state,
        all_events,
    ) -> None:
        """
        Runtime synchronization: re-label the completed vehicle as
        TRIP COMPLETED in the dashboard snapshot stream so the
        frontend can render the ACTIVE -> TRIP COMPLETED -> OFFLINE
        lifecycle. No analytics are computed here.
        """

        snapshot = runtime.dashboard_builder.mark_trip_completed(
            vehicle_id=summary.vehicle_id,
            completed_at=datetime.now(timezone.utc),
        )

        if snapshot is not None:
            snapshot_queue.put_nowait(snapshot)

    def _trip_flush(
        summary,
        context,
        runtime_state,
        all_events,
        trip,
    ) -> None:
        trip_publisher.publish(
            summary, context, runtime_state, all_events, trip
        )
        _dashboard_trip_completed(
            summary, context, runtime_state, all_events
        )

    def _trip_update(
        snapshots,
        now,
    ) -> None:
        trip_publisher.publish_active(
            snapshots,
            timestamp=now,
        )

    runtime.set_trip_flush_callback(
        _trip_flush
    )

    runtime.set_trip_update_callback(
        _trip_update
    )

    # --------------------------------------------------------------
    # Reconcile legacy duplicate pending maintenance records. Safe to
    # run on every boot: it only removes exact duplicate pending
    # projections per (vehicle_id, maintenance_type).
    # --------------------------------------------------------------

    try:
        await persistence_service.reconcile_maintenance_duplicates()
    except Exception:
        print(
            "Maintenance reconciliation failed at startup"
        )

    # --------------------------------------------------------------
    # Start background workers
    # --------------------------------------------------------------

    snapshot_worker_task = (
        asyncio.create_task(
            snapshot_worker()
        )
    )

    trips_worker_task = (
        asyncio.create_task(
            trips_worker()
        )
    )

    alerts_worker_task = (
        asyncio.create_task(
            alerts_worker()
        )
    )

    # --------------------------------------------------------------
    # Start DriveVitals runtime (default fleet, auto-start preserved.
    # The SimulationController owns the run task so a scenario launch can
    # stop and replace it.)
    # --------------------------------------------------------------

    await simulation_controller.start_default()

    print("DriveVitals runtime started")

    yield

    # --------------------------------------------------------------
    # Deterministic shutdown ordering (M5.2):
    #   1. stop accepting new runtime work (runtime.stop)
    #   2. cancel the simulation run task AND await it
    #   3. drain tracked background persistence tasks so every
    #      AsyncSession closes and its connection returns to the pool
    #   4. reconcile persisted state / stop broadcast workers
    #   5. dispose the SQLAlchemy engine while the loop is still alive
    #   6. let FastAPI/Uvicorn finish
    # Fire-and-forget cancellation here previously left in-flight
    # asyncpg work to the garbage collector, producing CancelledError
    # cascades and "non-checked-in connection" SAWarnings.
    # --------------------------------------------------------------

    await simulation_controller.shutdown()

    # Mark any scenario/run still flagged "running" as stopped so the
    # persisted Digital Twin lifecycle tracks reality.
    try:
        async with async_session_factory() as session:
            svc = DigitalTwinService(
                session,
                DriverRepository(session),
                VehicleRepository(session),
                RouteRepository(session),
                AssignmentRepository(session),
                ScenarioRepository(session),
                controller=simulation_controller,
            )
            await svc.complete_active_runs()
    except Exception:
        print("Digital Twin run completion failed at shutdown")

    # --------------------------------------------------------------
    # Stop background workers
    # --------------------------------------------------------------

    if snapshot_worker_task is not None:

        snapshot_worker_task.cancel()

        try:

            await snapshot_worker_task

        except asyncio.CancelledError:

            pass

    if trips_worker_task is not None:

        trips_worker_task.cancel()

        try:

            await trips_worker_task

        except asyncio.CancelledError:

            pass

    if alerts_worker_task is not None:

        alerts_worker_task.cancel()

        try:

            await alerts_worker_task

        except asyncio.CancelledError:

            pass

    # --------------------------------------------------------------
    # Unsubscribe dashboard publisher
    # --------------------------------------------------------------

    runtime.snapshot_stream.unsubscribe(
        snapshot_publisher
    )

    # --------------------------------------------------------------
    # Dispose the SQLAlchemy engine/pool. All sessions are closed and
    # all background tasks awaited by this point, so every pooled
    # connection can be closed cleanly instead of being torn down by
    # the garbage collector after the event loop is gone.
    # --------------------------------------------------------------

    await close_db()

    # flushed so the marker appears in order in a captured log (plain
    # print() is block-buffered when stdout is redirected to a file, which
    # would show it after uvicorn's own shutdown lines).
    print("DriveVitals runtime stopped", flush=True)


app = FastAPI(
    title="DriveVitals API",
    lifespan=lifespan,
)

# Comma-separated list of allowed browser origins. Defaults to the
# Dockerized Vite dev server on its standard port.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "*",
    ],
)


app.include_router(
    dashboard_router
)

app.include_router(
    trips_router
)

app.include_router(
    alerts_router
)

app.include_router(
    api_router
)


@app.get("/")
async def root() -> dict:

    return {
        "name": "DriveVitals",
        "status": "running",
    }
