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

from backend.dashboard.schemas.dashboard_payload import (
    DashboardSnapshot,
)


router = APIRouter()


snapshot_queue: asyncio.Queue[
    DashboardSnapshot
] = asyncio.Queue()


def _to_iso(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize(
    snapshot: DashboardSnapshot,
) -> dict:
    data = asdict(snapshot)
    data["timestamp"] = _to_iso(
        snapshot.timestamp
    )
    for v in data["vehicles"]:
        v["last_updated_at"] = _to_iso(
            v["last_updated_at"]
        )
        v["trip_started_at"] = _to_iso(
            v["trip_started_at"]
        )
    return data




async def snapshot_worker() -> None:
    """
    Broadcast frontend-ready dashboard snapshots.
    """

    while True:

        dashboard_snapshot = await (
            snapshot_queue.get()
        )

        try:

            payload = {
                "type": "dashboard_snapshot",
                "data": _serialize(
                    dashboard_snapshot
                ),
            }

            await websocket_manager.broadcast(
                payload
            )

        finally:

            snapshot_queue.task_done()


@router.websocket(
    "/ws/dashboard"
)
async def dashboard_websocket(
    websocket: WebSocket,
) -> None:

    await (
        websocket_manager.connect(
            websocket
        )
    )

    print(
        "🔌 Dashboard connected"
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        websocket_manager.disconnect(
            websocket
        )

        print(
            "❌ Dashboard disconnected"
        )