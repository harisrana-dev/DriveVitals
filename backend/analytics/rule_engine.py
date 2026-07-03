"""
DriveVitals Rule Engine

Evaluates incoming telemetry against predefined engineering
rules and generates standardized analytical events.

Version 1 uses deterministic rule-based analytics.
"""

from telemetry.models import TelemetryPacket


class RuleEngine:

    def __init__(self):

        # Engineering thresholds
        # (Later these will move to a config file.)

        self.MAX_SPEED = 120.0                 # km/h
        self.MAX_RPM = 5000                    # rpm
        self.MAX_ENGINE_LOAD = 85.0            # %
        self.MAX_COOLANT_TEMP = 105.0          # °C
        self.MAX_FUEL_RATE = 12.0              # L/h
        self.MAX_IDLE_RPM = 1000               # rpm

    # --------------------------------------------------

    def evaluate(self, packet: TelemetryPacket):

        events = []

        events.extend(self.check_overspeed(packet))
        events.extend(self.check_high_rpm(packet))
        events.extend(self.check_engine_load(packet))
        events.extend(self.check_coolant_temperature(packet))
        events.extend(self.check_fuel_rate(packet))
        events.extend(self.check_excessive_idle(packet))

        return events

    # --------------------------------------------------

    def create_event(
        self,
        rule_id,
        event,
        category,
        severity,
        value,
        threshold,
        packet
    ):

        return {

            "rule_id": rule_id,

            "event": event,

            "category": category,

            "severity": severity,

            "vehicle_id": packet.vehicle_id,

            "timestamp": packet.timestamp,

            "value": value,

            "threshold": threshold

        }

    # --------------------------------------------------

    def check_overspeed(self, packet):

        if packet.speed_kmh > self.MAX_SPEED:

            return [

                self.create_event(

                    "DV-R001",

                    "overspeed",

                    "driver_behaviour",

                    "WARNING",

                    packet.speed_kmh,

                    self.MAX_SPEED,

                    packet

                )

            ]

        return []

    # --------------------------------------------------

    def check_high_rpm(self, packet):

        if packet.rpm > self.MAX_RPM:

            return [

                self.create_event(

                    "DV-R002",

                    "high_rpm",

                    "vehicle_health",

                    "WARNING",

                    packet.rpm,

                    self.MAX_RPM,

                    packet

                )

            ]

        return []

    # --------------------------------------------------

    def check_engine_load(self, packet):

        if packet.engine_load > self.MAX_ENGINE_LOAD:

            return [

                self.create_event(

                    "DV-R003",

                    "high_engine_load",

                    "vehicle_health",

                    "WARNING",

                    packet.engine_load,

                    self.MAX_ENGINE_LOAD,

                    packet

                )

            ]

        return []

    # --------------------------------------------------

    def check_coolant_temperature(self, packet):

        if packet.coolant_temperature > self.MAX_COOLANT_TEMP:

            return [

                self.create_event(

                    "DV-R004",

                    "high_coolant_temperature",

                    "vehicle_health",

                    "CRITICAL",

                    packet.coolant_temperature,

                    self.MAX_COOLANT_TEMP,

                    packet

                )

            ]

        return []

    # --------------------------------------------------

    def check_fuel_rate(self, packet):

        if packet.fuel_rate_lph > self.MAX_FUEL_RATE:

            return [

                self.create_event(

                    "DV-R005",

                    "high_fuel_consumption",

                    "fuel_efficiency",

                    "WARNING",

                    packet.fuel_rate_lph,

                    self.MAX_FUEL_RATE,

                    packet

                )

            ]

        return []

    # --------------------------------------------------

    def check_excessive_idle(self, packet):

        if packet.speed_kmh < 1 and packet.rpm > self.MAX_IDLE_RPM:

            return [

                self.create_event(

                    "DV-R006",

                    "excessive_idle",

                    "driver_behaviour",

                    "INFO",

                    packet.rpm,

                    self.MAX_IDLE_RPM,

                    packet

                )

            ]

        return []