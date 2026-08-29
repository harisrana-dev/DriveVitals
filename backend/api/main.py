import asyncio

from contextlib import asynccontextmanager

from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    FastAPI,
)

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

from backend.api.websocket.trip_publisher import (
    TripSnapshotPublisher,
)

from backend.api.v1.services.admin_bootstrap import (
    AdminBootstrapConfigError,
    bootstrap_admin,
)

from backend.db.persistence_service import (
    PersistenceService,
)

from backend.db.session import (
    async_session_factory,
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

runtime_task: asyncio.Task | None = None

snapshot_worker_task: asyncio.Task | None = None

trips_worker_task: asyncio.Task | None = None

alerts_worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    global runtime_task
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
    # Start DriveVitals runtime
    # --------------------------------------------------------------

    runtime_task = (
        asyncio.create_task(
            runtime.run()
        )
    )

    print("DriveVitals runtime started")

    yield

    # --------------------------------------------------------------
    # Stop DriveVitals runtime
    # --------------------------------------------------------------

    runtime.stop()

    if runtime_task is not None:

        runtime_task.cancel()

        try:

            await runtime_task

        except asyncio.CancelledError:

            pass

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

    print("DriveVitals runtime stopped")


app = FastAPI(
    title="DriveVitals API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
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
