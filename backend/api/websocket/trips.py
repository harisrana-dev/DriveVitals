"""
WebSocket endpoint and worker for the trips channel.

The trips channel broadcasts two kinds of snapshots:

1. Active-trip updates (``publish_active``) — once per tick, containing
   only currently active trips.
2. Completed-trip updates (``publish``) — emitted when a trip finishes,
   containing the full updated set of completed trips.

Both are serialized and broadcast by ``trips_worker``.
"""

import asyncio

from dataclasses import asdict

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from backend.api.dependencies import (
    websocket_manager,
)

from backend.api.websocket.security import (
    WS_AUTH_REJECT_CODE,
    WS_AUTH_REJECT_REASON,
    authenticate_ws,
)

from backend.db.session import (
    async_session_factory,
)

from backend.trips.schemas.trip_payload import (
    TripsSnapshot,
)


router = APIRouter()


trips_queue: asyncio.Queue[
    TripsSnapshot
] = asyncio.Queue()


def _serialize(
    snapshot: TripsSnapshot,
) -> dict:
    data = asdict(snapshot)
    data["timestamp"] = (
        snapshot.timestamp.isoformat()
        if snapshot.timestamp is not None
        else None
    )
    trips = []
    for t in data["trips"]:
        t["started_at"] = (
            t["started_at"].isoformat()
            if t["started_at"] is not None
            else None
        )
        t["completed_at"] = (
            t["completed_at"].isoformat()
            if t["completed_at"] is not None
            else None
        )
        trips.append(t)
    data["trips"] = trips
    return data


async def trips_worker() -> None:
    while True:
        trips_snapshot = await (
            trips_queue.get()
        )
        try:
            payload = {
                "type": "trips_snapshot",
                "data": _serialize(
                    trips_snapshot
                ),
            }
            await websocket_manager.broadcast(
                payload
            )
        finally:
            trips_queue.task_done()


@router.websocket(
    "/ws/trips"
)
async def trips_websocket(
    websocket: WebSocket,
) -> None:
    # Authenticate with a short-lived DB session and release it before the
    # long-lived receive loop. Holding an AsyncSession open for the whole
    # socket lifetime pins a pooled connection per client and produces
    # greenlet/finalizer warnings on shutdown.
    async with async_session_factory() as session:
        user = await authenticate_ws(
            websocket,
            session,
        )

    if user is None:

        await websocket.close(
            code=WS_AUTH_REJECT_CODE,
            reason=WS_AUTH_REJECT_REASON,
        )

        return

    await (
        websocket_manager.connect(
            websocket
        )
    )
    print(
        "Trips WebSocket connected"
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(
            websocket
        )
        print(
            "Trips WebSocket disconnected"
        )
