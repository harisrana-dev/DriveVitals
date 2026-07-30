import asyncio

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
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

from backend.api.websocket.snapshot_publisher import (
    DashboardSnapshotPublisher,
)

from backend.api.websocket.trip_publisher import (
    TripSnapshotPublisher,
)

from backend.db.persistence_service import (
    PersistenceService,
)

from backend.trips.store.trip_store import (
    TripStore,
)

from backend.trips.services.trip_builder import (
    TripBuilder,
)


runtime = (
    DriveVitalsRuntime(
        persistence_service=PersistenceService()
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


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    global runtime_task
    global snapshot_worker_task
    global trips_worker_task

    # --------------------------------------------------------------
    # Connect analytics snapshot stream to dashboard queue
    # --------------------------------------------------------------

    runtime.snapshot_stream.subscribe(
        snapshot_publisher
    )

    # --------------------------------------------------------------
    # Register trip flush callback
    # --------------------------------------------------------------

    runtime.set_trip_flush_callback(
        trip_publisher.publish
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

    # --------------------------------------------------------------
    # Start DriveVitals runtime
    # --------------------------------------------------------------

    runtime_task = (
        asyncio.create_task(
            runtime.run()
        )
    )

    print(
        "🚗 DriveVitals runtime started"
    )

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

    # --------------------------------------------------------------
    # Unsubscribe dashboard publisher
    # --------------------------------------------------------------

    runtime.snapshot_stream.unsubscribe(
        snapshot_publisher
    )

    print(
        "🛑 DriveVitals runtime stopped"
    )


app = FastAPI(
    title="DriveVitals API",
    lifespan=lifespan,
)


app.include_router(
    dashboard_router
)

app.include_router(
    trips_router
)


@app.get("/")
async def root() -> dict:

    return {
        "name": "DriveVitals",
        "status": "running",
    }
