from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from backend.api.websocket.manager import (
    WebSocketManager,
)
# routes.py

from backend.api.dependencies import (
    websocket_manager,
)


router = APIRouter()


@router.websocket(
    "/ws/dashboard"
)
async def dashboard_websocket(
    websocket: WebSocket,
) -> None:

    await websocket_manager.connect(
        websocket
    )

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        websocket_manager.disconnect(
            websocket
        )