import asyncio
import os

import websockets


def _uri() -> str:
    token = os.environ.get("DRIVEVITALS_TOKEN")
    if not token:
        raise SystemExit(
            "DRIVEVITALS_TOKEN is required: the dashboard WebSocket now "
            "rejects anonymous connections. Log in via POST /api/v1/auth/login "
            "and export the returned token as DRIVEVITALS_TOKEN."
        )
    return (
        "ws://127.0.0.1:8000/ws/dashboard"
        f"?token={token}"
    )


async def client(
    client_name: str,
) -> None:

    print(
        f"[{client_name}] Connecting..."
    )

    async with websockets.connect(
        _uri()
    ) as websocket:

        print(
            f"[{client_name}] Connected"
        )

        message_count = 0

        while True:

            await websocket.recv()

            message_count += 1

            if (
                message_count
                % 10
                == 0
            ):

                print(
                    f"[{client_name}] "
                    f"received "
                    f"{message_count} "
                    f"snapshots"
                )


async def main() -> None:

    await asyncio.gather(

        client(
            "CLIENT-1"
        ),

        client(
            "CLIENT-2"
        ),

        client(
            "CLIENT-3"
        ),
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )