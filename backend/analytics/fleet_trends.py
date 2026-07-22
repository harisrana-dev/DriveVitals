"""FleetTrendAnalyzer: fleet-wide aggregated trends from AnalyticsInput.

Computes rolling averages of available signals across all vehicles.
Does not depend on the old state manager's V1 fields.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime

from analytics.analytics_input import AnalyticsInput


class FleetTrendAnalyzer:
    """Tracks fleet-wide trends over a sliding window."""

    def __init__(self, max_history: int = 30) -> None:
        self._history: deque[dict] = deque(maxlen=max_history)

    def update(self, inputs: dict[str, AnalyticsInput]) -> list[dict]:
        """Compute fleet-wide averages and append to history.

        Args:
            inputs: Map of vehicle_id -> latest AnalyticsInput per vehicle.

        Returns:
            Full history list (newest last).
        """
        if not inputs:
            return list(self._history)

        speeds: list[float] = []
        temps: list[float] = []
        loads: list[float] = []
        batteries: list[float] = []

        for ai in inputs.values():
            if ai.speed_kmh is not None:
                speeds.append(ai.speed_kmh)
            if ai.engine_temperature_celsius is not None:
                temps.append(ai.engine_temperature_celsius)
            if ai.engine_load_percent is not None:
                loads.append(ai.engine_load_percent)
            if ai.battery_voltage is not None:
                batteries.append(ai.battery_voltage)

        snapshot: dict = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "vehicle_count": len(inputs),
        }

        if speeds:
            snapshot["avg_speed_kmh"] = round(sum(speeds) / len(speeds), 2)
        if temps:
            snapshot["avg_engine_temperature_c"] = round(sum(temps) / len(temps), 2)
        if loads:
            snapshot["avg_engine_load_percent"] = round(sum(loads) / len(loads), 2)
        if batteries:
            snapshot["avg_battery_voltage"] = round(sum(batteries) / len(batteries), 2)

        self._history.append(snapshot)
        return list(self._history)
