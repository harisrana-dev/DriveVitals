import asyncio
import json
import websockets

# -------------------------------
# Simulator Imports
# (Adjust these filenames if needed)
# -------------------------------

from simulator.city_car_simulator import VehicleSimulator as CityCarSimulator
from simulator.aggressive_driver_simulator import VehicleSimulator as AggressiveSimulator
from simulator.highway_vehicle_simulator import VehicleSimulator as HighwaySimulator
from simulator.delivery_van_simulator import VehicleSimulator as DeliveryVanSimulator

from fleet.vehicle_registry import VEHICLES

WS_URL = "ws://127.0.0.1:8000/ws/telemetry"


class FleetManager:

    def __init__(self):

        self.simulators = [
            (
                CityCarSimulator(update_hz=5),
                VEHICLES[0]
            ),
            (
                AggressiveSimulator(update_hz=5),
                VEHICLES[1]
            ),
            (
                HighwaySimulator(update_hz=5),
                VEHICLES[2]
            ),
            (
                DeliveryVanSimulator(update_hz=5),
                VEHICLES[3]
            )
        ]

    async def stream_vehicle(self, websocket, simulator, metadata):

        async for telemetry in simulator.stream_async():

            # Override metadata coming from simulator
            telemetry["vehicle_id"] = metadata["vehicle_id"]
            telemetry["driver_id"] = metadata["driver_id"]
            telemetry["vehicle_type"] = metadata["vehicle_type"]

            # Optional (future expansion)
            telemetry["fleet_id"] = "FLEET001"

            await websocket.send(json.dumps(telemetry))

            print(
                f"📤 "
                f"{telemetry['vehicle_id']} | "
                f"{telemetry['speed_kmh']} km/h | "
                f"RPM {telemetry['rpm']}"
            )

    async def run(self):

        async with websockets.connect(WS_URL) as websocket:

            print("\n===================================")
            print(" DriveVitals Fleet Manager Started ")
            print("===================================\n")

            tasks = []

            for simulator, metadata in self.simulators:

                tasks.append(

                    asyncio.create_task(
                        self.stream_vehicle(
                            websocket,
                            simulator,
                            metadata
                        )
                    )

                )

            await asyncio.gather(*tasks)


async def main():

    manager = FleetManager()

    await manager.run()


if __name__ == "__main__":
    asyncio.run(main())