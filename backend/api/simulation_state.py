"""Module-level simulation state shared between the app entrypoint and
the API dependency layer.

:class:`SimulationController` wraps the single live runtime instance and
owns its task lifecycle. It is created once at import time by
``api/main.py`` and exposed here so the digital-twin routers/services can
reach it without a circular import.

In test environments where the full app is not wired up, these remain
``None``; the digital-twin launch endpoints simply report "not running".
"""

from backend.application.runtime import DriveVitalsRuntime
from backend.application.simulation_controller import SimulationController

runtime: DriveVitalsRuntime | None = None
simulation_controller: SimulationController | None = None


def init_simulation_controller(
    runtime_instance: DriveVitalsRuntime,
) -> SimulationController:
    """Attach the live runtime and create the controller singleton."""
    global runtime, simulation_controller
    runtime = runtime_instance
    simulation_controller = SimulationController(runtime_instance)
    return simulation_controller
