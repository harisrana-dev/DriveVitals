import asyncio

import websockets


URI = (
    "ws://127.0.0.1:8000/ws/dashboard"
)


async def client(
    client_name: str,
) -> None:

    print(
        f"[{client_name}] Connecting..."
    )

    async with websockets.connect(
        URI
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