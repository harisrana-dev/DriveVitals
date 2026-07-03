"""
DriveVitals Telemetry Dispatcher

Receives incoming telemetry, validates it,
and forwards valid packets to the telemetry processor.
"""

from telemetry.models import TelemetryPacket
from telemetry.validator import TelemetryValidator
from telemetry.processor import TelemetryProcessor


class TelemetryDispatcher:

    def __init__(self):
        self.validator = TelemetryValidator()
        self.processor = TelemetryProcessor()

    def dispatch(self, telemetry_data: dict):

        try:

            # Convert incoming dictionary
            # into our canonical telemetry model

            packet = TelemetryPacket(**telemetry_data)

        except Exception as e:

            print(f"❌ Invalid telemetry format: {e}")
            return

        # Validate engineering ranges

        if not self.validator.validate(packet):

            print(
                f"❌ Validation failed for vehicle "
                f"{packet.vehicle_id}"
            )

            return

        # Forward to processor

        self.processor.process(packet)