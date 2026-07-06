"""
DriveVitals Vehicle State Manager

Maintains the latest live state of every connected vehicle.

The State Manager serves as the single source of truth for
real-time dashboard data. Each vehicle has exactly one
VehicleState object which is continuously updated as new
telemetry is processed.
"""

import asyncio
from datetime import datetime,timezone
from dataclasses import asdict
from dashboard.connection_manager import dashboard_manager
from state.vehicle_state import VehicleState



class VehicleStateManager:

    def __init__(self):

        # Dictionary of all live vehicles
        # Key = vehicle_id
        # Value = VehicleState

        self.states: dict[str, VehicleState] = {}

    # --------------------------------------------------

    def update_state(
        self,
        packet,
        analytics_results
    ):

        vehicle_id = packet.vehicle_id

        if vehicle_id not in self.states:

            self.states[vehicle_id] = VehicleState(
                vehicle_id=vehicle_id
            )

        state = self.states[vehicle_id]

        # Latest telemetry
        state.telemetry = packet.model_dump()

        # Analytics
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

        # Broadcast updated vehicle state
        try:
           asyncio.create_task(
               dashboard_manager.broadcast({
                    "type": "vehicle_update",
                    "vehicle": asdict(state)
                })
            )
        except RuntimeError:
            # No running event loop (mainly during testing)
            pass

    # --------------------------------------------------

    def get_vehicle(self, vehicle_id):

        return self.states.get(vehicle_id)

    # --------------------------------------------------

    def get_all_vehicles(self):
        return dict(self.states)

    # --------------------------------------------------

    def remove_vehicle(self, vehicle_id):

        if vehicle_id in self.states:
            del self.states[vehicle_id]

    # --------------------------------------------------

    def vehicle_count(self):

        return len(self.states)
    
    # Global singleton instance

state_manager = VehicleStateManager()