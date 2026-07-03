"""
DriveVitals Telemetry Validator

Validates incoming telemetry packets before they enter
the analytics engine.
"""

from telemetry.models import TelemetryPacket


class TelemetryValidator:

    @staticmethod
    def validate(packet: TelemetryPacket) -> bool:
        """
        Returns True if the telemetry packet passes all
        validation rules.
        """

        # -------------------------
        # Vehicle Metadata
        # -------------------------

        if not packet.vehicle_id:
            return False

        if not packet.driver_id:
            return False

        if not packet.fleet_id:
            return False

        # -------------------------
        # Speed
        # -------------------------

        if packet.speed_kmh < 0:
            return False

        if packet.speed_kmh > 250:
            return False

        # -------------------------
        # RPM
        # -------------------------

        if packet.rpm < 0:
            return False

        if packet.rpm > 9000:
            return False

        # -------------------------
        # Gear
        # -------------------------

        if packet.gear < 0:
            return False

        if packet.gear > 8:
            return False

        # -------------------------
        # Throttle
        # -------------------------

        if packet.throttle_position < 0:
            return False

        if packet.throttle_position > 100:
            return False

        # -------------------------
        # Engine Load
        # -------------------------

        if packet.engine_load < 0:
            return False

        if packet.engine_load > 100:
            return False

        # -------------------------
        # Coolant Temperature
        # -------------------------

        if packet.coolant_temperature < -40:
            return False

        if packet.coolant_temperature > 150:
            return False

        # -------------------------
        # Fuel Rate
        # -------------------------

        if packet.fuel_rate_lph < 0:
            return False

        if packet.fuel_rate_lph > 100:
            return False

        return True