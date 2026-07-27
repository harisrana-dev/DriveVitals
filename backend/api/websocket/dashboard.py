import asyncio

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from backend.analytics.snapshot.analytics_snapshot import (
    AnalyticsSnapshot,
)

from backend.api.dependencies import (
    websocket_manager,
)


router = APIRouter()


snapshot_queue: asyncio.Queue[
    AnalyticsSnapshot
] = asyncio.Queue()


def build_dashboard_payload(
    snapshot: AnalyticsSnapshot,
) -> dict:
    """
    Convert an AnalyticsSnapshot into
    a dashboard-facing JSON payload.
    """

    telemetry = (
        snapshot.telemetry
    )

    behaviour = (
        snapshot.behaviour
    )

    return {
        "type": "analytics_snapshot",

        "vehicle_id": (
            snapshot.vehicle_id
        ),

        "driver_id": (
            snapshot.driver_id
        ),

        "trip_id": (
            snapshot.trip_id
        ),

        "timestamp": (
            snapshot.timestamp.isoformat()
        ),

        "telemetry": {
            "speed_kmh": (
                telemetry.speed_kmh
            ),

            "rpm": (
                telemetry.rpm
            ),

            "engine_load_percent": (
                telemetry.engine_load_percent
            ),

            "throttle_position_percent": (
                telemetry.throttle_position_percent
            ),

            "brake_pressure": (
                telemetry.brake_pressure
            ),

            "coolant_temperature_c": (
                telemetry.coolant_temperature_c
            ),

            "fuel_rate_lph": (
                telemetry.fuel_rate_lph
            ),

            "fuel_level_percent": (
                telemetry.fuel_level_percent
            ),

            "odometer_km": (
                telemetry.odometer_km
            ),
        },

        "behaviour": {
            "speeding": (
                behaviour.speeding
            ),

            "harsh_braking": (
                behaviour.harsh_braking
            ),

            "aggressive_throttle": (
                behaviour.aggressive_throttle
            ),

            "high_rpm": (
                behaviour.high_rpm
            ),

            "speed_excess_kmh": (
                behaviour.speed_excess_kmh
            ),

            "severity": (
                behaviour.severity
            ),
        },

        "events": {
            "completed": [
                {
                    "event_type": (
                        event.event_type
                    ),

                    "started_at": (
                        event.started_at.isoformat()
                    ),

                    "ended_at": (
                        event.ended_at.isoformat()
                    ),

                    "duration_seconds": (
                        event.duration_seconds
                    ),

                    "distance_km": (
                        event.distance_km
                    ),

                    "severity": (
                        event.severity
                    ),
                }

                for event
                in snapshot.completed_events
            ],

            "active": list(
                snapshot.active_event_types
            ),
        },
    }


async def snapshot_worker() -> None:
    """
    Continuously consumes analytics snapshots
    and broadcasts them to dashboard clients.
    """

    while True:

        snapshot = await (
            snapshot_queue.get()
        )

        try:

            payload = (
                build_dashboard_payload(
                    snapshot
                )
            )

            await (
                websocket_manager.broadcast(
                    payload
                )
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