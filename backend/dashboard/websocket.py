import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from dashboard.connection_manager import dashboard_manager

async def dashboard_websocket(websocket: WebSocket):
    await dashboard_manager.connect(websocket)
    print("➡️ Entered dashboard loop")

    try:
        while True:
            await asyncio.sleep(5)
            print("❤️ Dashboard alive")
    except WebSocketDisconnect:
        print("💥 Dashboard WebSocketDisconnect")
        dashboard_manager.disconnect(websocket)
    except Exception as e:
        print("💥 Dashboard exception:", repr(e))