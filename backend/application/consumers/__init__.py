"""
Application-level fleet intelligence consumers.

Consumers bridge the existing runtime flows (TelemetryPipeline and
trip completion) into the intelligence engines, writing their outputs
to the shared IntelligenceState.
"""

from backend.application.consumers.driver_statistics_consumer import (
    DriverStatisticsConsumer,
)
from backend.application.consumers.vehicle_health_consumer import (
    VehicleHealthConsumer,
)

__all__ = [
    "VehicleHealthConsumer",
    "DriverStatisticsConsumer",
]
