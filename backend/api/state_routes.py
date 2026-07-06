"""
DriveVitals State API

Exposes the latest live vehicle states stored in RAM.

The State API provides read-only access to the
Vehicle State Manager and serves as the primary
backend interface for dashboards and monitoring tools.
"""

from fastapi import APIRouter, HTTPException
from dataclasses import asdict

from state.state_manager import state_manager

router = APIRouter()


# --------------------------------------------------


@router.get("/state")
def get_all_vehicle_states():

    vehicles = {
        vehicle_id: asdict(state)
        for vehicle_id, state in state_manager.get_all_vehicles().items()
    }

    return {
        "status": "success",
        "vehicle_count": state_manager.vehicle_count(),
        "vehicles": vehicles
    }


# --------------------------------------------------


@router.get("/state/{vehicle_id}")
def get_vehicle_state(vehicle_id: str):

    state = state_manager.get_vehicle(vehicle_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle '{vehicle_id}' not found."
        )

    return {
        "status": "success",
        "vehicle": asdict(state)
    }


# --------------------------------------------------


@router.get("/state/health")
def state_health():

    return {
        "status": "running",
        "vehicles": state_manager.vehicle_count()
    }