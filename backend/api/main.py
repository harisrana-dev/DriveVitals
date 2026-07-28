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

from backend.api.websocket.snapshot_publisher import (
    DashboardSnapshotPublisher,
)


runtime = (
    DriveVitalsRuntime()
)

snapshot_publisher = DashboardSnapshotPublisher(
    queue=snapshot_queue,
    builder=runtime.dashboard_builder,
)

runtime_task: asyncio.Task | None = None

snapshot_worker_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    global runtime_task
    global snapshot_worker_task

    # --------------------------------------------------------------
    # Connect analytics snapshot stream to dashboard queue
    # --------------------------------------------------------------

    runtime.snapshot_stream.subscribe(
        snapshot_publisher
    )

    # --------------------------------------------------------------
    # Start dashboard snapshot worker
    # --------------------------------------------------------------

    snapshot_worker_task = (
        asyncio.create_task(
            snapshot_worker()
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
    # Stop snapshot worker
    # --------------------------------------------------------------

    if snapshot_worker_task is not None:

        snapshot_worker_task.cancel()

        try:

            await snapshot_worker_task

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


@app.get("/")
async def root() -> dict:

    return {
        "name": "DriveVitals",
        "status": "running",
    }
