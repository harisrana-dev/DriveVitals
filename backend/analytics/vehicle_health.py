class VehicleHealthAnalyzer:

    def analyze(self, packet, rules):
        return {
            "status": "ok",
            "engine_temp": getattr(packet, "coolant_temperature", None),
            "rpm": getattr(packet, "rpm", None),
            "speed": getattr(packet, "speed_kmh", None),
            "fuel_level": getattr(packet, "fuel_rate_lph", None),
            "health": "healthy"
        }