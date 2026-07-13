"""
DriveVitals Maintenance Queue Analyzer

Generates maintenance recommendations based on
vehicle operating conditions.

This analyzer is rule-based for Sprint 1 and will
later evolve into predictive maintenance.
"""


class MaintenanceQueueAnalyzer:

    def analyze(
        self,
        packet,
        analytics_results,
    ):

        maintenance = []

        health = analytics_results.get(
            "vehicle_health",
            {}
        )

        fuel = analytics_results.get(
            "fuel_efficiency",
            {}
        )

        # ----------------------------------
        # Cooling System
        # ----------------------------------

        if packet.coolant_temperature >= 100:

            maintenance.append({

                "vehicle_id": packet.vehicle_id,

                "priority": "High",

                "maintenance": "Cooling System Inspection",

                "remaining": "Immediate",

            })

        # ----------------------------------
        # Engine Load
        # ----------------------------------

        if packet.engine_load >= 85 and packet.rpm > 3500:

            maintenance.append({

                "vehicle_id": packet.vehicle_id,

                "priority": "Medium",

                "maintenance": "Engine Inspection",

                "remaining": "500 km",

            })

        # ----------------------------------
        # Fuel Efficiency
        # ----------------------------------

        if fuel.get("rating") == "poor":

            maintenance.append({

                "vehicle_id": packet.vehicle_id,

                "priority": "Medium",

                "maintenance": "Air Filter / Injector Check",

                "remaining": "700 km",

            })

        # ----------------------------------
        # Vehicle Health
        # ----------------------------------

        if health.get("health") == "critical":

            maintenance.append({

                "vehicle_id": packet.vehicle_id,

                "priority": "High",

                "maintenance": "Immediate Workshop Visit",

                "remaining": "Immediate",

            })

        return maintenance