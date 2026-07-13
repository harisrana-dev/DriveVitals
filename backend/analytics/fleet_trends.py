from collections import deque
from datetime import datetime


class FleetTrendAnalyzer:

    def __init__(self):

        # Last 30 snapshots
        self.history = deque(maxlen=30)

    def update(self, state_manager):

        vehicles = state_manager.get_all_vehicles().values()

        if not vehicles:
            return list(self.history)

        fuel_values = []

        for vehicle in vehicles:

            fuel = (
                vehicle.fuel_efficiency
                .get("km_per_liter")
            )

            if fuel is not None:
                fuel_values.append(fuel)

        if not fuel_values:
            return list(self.history)

        average = round(
            sum(fuel_values) / len(fuel_values),
            2
        )

        self.history.append(

            {

                "time": datetime.now().strftime("%H:%M:%S"),

                "fuel_efficiency": average,

            }

        )

        return list(self.history)