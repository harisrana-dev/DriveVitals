"""
WebSocket endpoint and worker for the alerts channel.

Broadcasts alert lifecycle events:
- alert_created: new alert (or updated open alert) emitted by generators
- alert_acknowledged: alert acknowledged by user
- alert_resolved: alert resolved (auto or manual)

Event payloads are keyed by the stored, vehicle-scoped ``alert_id`` so the
frontend can reconcile them against REST rows (see ``AlertRepository``).
"""

import asyncio

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from backend.api.dependencies import (
    websocket_manager,
)


router = APIRouter()


alerts_queue: asyncio.Queue[dict] = asyncio.Queue()


def _to_iso(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def publish_alert_row(event_type: str, alert) -> None:
    """Enqueue a serialized lifecycle event for a stored Alert row.

    ``alert`` is an ORM ``Alert`` whose ``alert_id`` is the vehicle-scoped
    id used by the REST API. ``put_nowait`` is safe here: the worker drains
    the queue continuously and the payload is fully serialized.
    """
    alerts_queue.put_nowait(
        {
            "type": event_type,
            "alert_id": alert.alert_id,
            "vehicle_id": alert.vehicle_id,
            "driver_id": alert.driver_id,
            "trip_id": alert.trip_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status,
            "acknowledged": alert.acknowledged,
            "acknowledged_at": _to_iso(alert.acknowledged_at),
            "created_at": _to_iso(alert.created_at),
            "resolved_at": _to_iso(alert.resolved_at),
            "condition": alert.condition,
            "category": alert.category,
            "message": alert.message,
            "evidence": alert.evidence,
            "source": alert.source,
        }
    )


async def alerts_worker() -> None:
    """Broadcast alert events to connected WebSocket clients."""

    while True:
        event = await alerts_queue.get()
        try:
            payload = {
                "type": "alert_event",
                "data": event,
            }
            await websocket_manager.broadcast(payload)
        finally:
            alerts_queue.task_done()


@router.websocket(
    "/ws/alerts"
)
async def alerts_websocket(
    websocket: WebSocket,
) -> None:
    await (
        websocket_manager.connect(
            websocket
        )
    )

    print(
        "🔌 Alerts WebSocket connected"
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(
            websocket
        )
        print(
            "❌ Alerts WebSocket disconnected"
        )
