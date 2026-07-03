class FuelEfficiencyAnalyzer:

    def analyze(self, packet, rules):

        speed = getattr(packet, "speed_kmh", 0)
        fuel = getattr(packet, "fuel_rate_lph", 0)

        if fuel == 0:
            efficiency = 0
        else:
            efficiency = speed / (fuel + 0.01)

        return {
            "status": "ok",
            "fuel_rate": fuel,
            "speed": speed,
            "efficiency_score": round(efficiency, 2)
        }