class FuelEfficiencyAnalyzer:

    def analyze(self, packet, rules):

        speed = getattr(packet, "speed_kmh", 0)
        fuel_rate = getattr(packet, "fuel_rate_lph", 0)


        # Vehicle is idling
        if speed < 5:

            return {

                "status": "ok",

                "mode": "idle",

                "fuel_rate_lph": round(fuel_rate,2),

                "idle_consumption_lph": round(fuel_rate,2),

                "km_per_liter": None,

                "rating": "idle"

            }


        # Vehicle is moving

        if fuel_rate <= 0:

            km_per_liter = 0

        else:

            km_per_liter = speed / fuel_rate



        if km_per_liter >= 15:

            rating = "excellent"

        elif km_per_liter >= 10:

            rating = "good"

        elif km_per_liter >= 5:

            rating = "average"

        else:

            rating = "poor"



        return {

            "status": "ok",

            "mode": "driving",

            "fuel_rate_lph": round(fuel_rate,2),

            "speed_kmh": round(speed,2),

            "km_per_liter": round(km_per_liter,2),

            "rating": rating

        }