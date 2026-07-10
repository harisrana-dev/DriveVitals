"""
DriveVitals Vehicle State Manager

Maintains the latest live state of every connected vehicle.

The State Manager serves as the single source of truth for
real-time dashboard data. Each vehicle has exactly one
VehicleState object which is continuously updated as new
telemetry is processed.
"""

import asyncio
from datetime import datetime, timezone
from dataclasses import asdict
from fastapi.encoders import jsonable_encoder
from dashboard.connection_manager import dashboard_manager
from state.vehicle_state import VehicleState
from collections import deque
from analytics.event_metadata import enrich_event


class VehicleStateManager:
    """
    Maintains the latest live state of every connected vehicle.
    """

    def __init__(self):

        # Key   -> vehicle_id
        # Value -> VehicleState

        self.states: dict[str, VehicleState] = {}

        # Global event history (newest first)
        self.events = deque(maxlen=200)

        # Fast lookup for duplicate events
        self.event_index = {}

    # --------------------------------------------------

    def update_state(
        self,
        packet,
        analytics_results,
    ) -> VehicleState:
        """
        Update the live state for a vehicle and broadcast
        the latest state to all connected dashboard clients.
        """

        vehicle_id = packet.vehicle_id

        if vehicle_id not in self.states:
            self.states[vehicle_id] = VehicleState(
                vehicle_id=vehicle_id
            )

        state = self.states[vehicle_id]

        # -----------------------------
        # Latest telemetry
        # -----------------------------

        state.telemetry = packet.model_dump()
        # -----------------------------
        # Vehicle Status
        # -----------------------------

        if packet.speed_kmh > 1:

            state.status = "active"

        elif packet.rpm > 0:

            state.status = "idle"

        else:

           state.status = "offline"


        # -----------------------------
        # Analytics
        # -----------------------------

        state.driver_behaviour = analytics_results.get(
            "driver_behaviour", {}
        )

        state.vehicle_health = analytics_results.get(
            "vehicle_health", {}
        )

        state.fuel_efficiency = analytics_results.get(
            "fuel_efficiency", {}
        )

        state.trip_performance = analytics_results.get(
            "trip_performance", {}
        )

        state.driver_ranking = analytics_results.get(
             "driver_ranking",
             state.driver_ranking
        )
        print("🏆 Driver Ranking:", state.driver_ranking)
        

        state.alerts = analytics_results.get(
            "rules", []
        )
        new_events = analytics_results.get("rules", [])


        for raw_event in new_events:

            event = raw_event.copy()
            event["vehicle_id"] = packet.vehicle_id
            event["driver_id"] = packet.driver_id
            event = enrich_event(event)
            


            event_key = (
               event["vehicle_id"],
               event["event"]
            )


            if event_key in self.event_index:


               existing = self.event_index[event_key]

               existing["occurrences"] += 1

               existing["timestamp"] = event["timestamp"]

               existing["value"] = event["value"]


            else:

              event["occurrences"] = 1

              self.events.appendleft(event)

              self.event_index[event_key] = event
        print("Event history size:", len(self.events))

        # -----------------------------
        # Timestamp
        # -----------------------------

        state.last_updated = datetime.now(timezone.utc)
        
        # -----------------------------
        # Broadcast updated state
        # -----------------------------
        print(asdict(state))
        try:
            print("Broadcasting...")
            asyncio.create_task(
                
                
                dashboard_manager.broadcast(
                    {
                        "type": "dashboard_update",
                        "vehicle": jsonable_encoder(state),
                        "recent_events": jsonable_encoder(
                           self.get_recent_events()
                        ),
                    }
                )
            )
            print("Broadcast queued")

        except RuntimeError:
            # Happens only when no event loop exists
            # (typically during isolated testing).
            pass

        return state

    # --------------------------------------------------
    def get_recent_events(self):

       return list(self.events)

    def get_vehicle(
        self,
        vehicle_id: str,
    ) -> VehicleState | None:

        return self.states.get(vehicle_id)

    # --------------------------------------------------

    def get_all_vehicles(
        self,
    ) -> dict[str, VehicleState]:

        return dict(self.states)

    # --------------------------------------------------

    def remove_vehicle(
        self,
        vehicle_id: str,
    ):

        if vehicle_id in self.states:
            del self.states[vehicle_id]

    # --------------------------------------------------

    def vehicle_count(self) -> int:

        return len(self.states)


# ------------------------------------------------------
# Global singleton
# ------------------------------------------------------

state_manager = VehicleStateManager()