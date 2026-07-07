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


class VehicleStateManager:
    """
    Maintains the latest live state of every connected vehicle.
    """

    def __init__(self):

        # Key   -> vehicle_id
        # Value -> VehicleState

        self.states: dict[str, VehicleState] = {}

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

        state.alerts = analytics_results.get(
            "rules", []
        )

        # -----------------------------
        # Timestamp
        # -----------------------------

        state.last_updated = datetime.now(timezone.utc)
        
        print("STATE MANAGER:", id(self))
        print("DASHBOARD MANAGER:", id(dashboard_manager))
        print("ACTIVE:", len(dashboard_manager.active_connections))
        # -----------------------------
        # Broadcast updated state
        # -----------------------------
        print(asdict(state))
        try:
            asyncio.create_task(
                
                dashboard_manager.broadcast(
                    {
                        "type": "vehicle_update",
                        "vehicle": jsonable_encoder(state),
                    }
                )
            )

        except RuntimeError:
            # Happens only when no event loop exists
            # (typically during isolated testing).
            pass

        return state

    # --------------------------------------------------

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