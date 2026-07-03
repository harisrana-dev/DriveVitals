"""
DriveVitals Telemetry Processor

Receives validated telemetry packets from the dispatcher
and forwards them to the Analytics Engine.

This class acts as the bridge between the telemetry
module and the analytics module.
"""

from telemetry.models import TelemetryPacket
from analytics.engine import AnalyticsEngine


class TelemetryProcessor:

    def __init__(self):
        self.analytics_engine = AnalyticsEngine()

    def process(self, packet: TelemetryPacket):
        """
        Process a validated telemetry packet.

        Parameters
        ----------
        packet : TelemetryPacket
            Validated telemetry packet.
        """

        self.analytics_engine.process(packet)