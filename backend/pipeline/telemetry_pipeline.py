"""
Telemetry Pipeline.

Receives raw TelemetrySample objects produced by the fleet runtime
and distributes them to registered consumers.

The pipeline does not:
    - generate telemetry
    - interpret driver behavior
    - perform analytics
    - access a database directly
    - know about dashboards

It is only responsible for routing telemetry to consumers.

Example flow:

    Fleet Runtime
          │
          ▼
    TelemetrySample
          │
          ▼
    TelemetryPipeline
          │
          ├──► Analytics Engine
          ├──► Persistence Consumer
          └──► WebSocket Consumer
"""


from typing import Protocol

from backend.telemetry.models.telemetry_sample import TelemetrySample


class TelemetryConsumer(Protocol):
    """
    Contract for anything that consumes telemetry.

    Analytics engines, database writers, WebSocket publishers,
    and future consumers can implement this contract.
    """

    def consume(self, sample: TelemetrySample) -> None:
        ...


class TelemetryPipeline:
    """
    Central distribution point for raw telemetry.

    The pipeline receives a TelemetrySample and forwards it to every
    registered consumer.
    """

    def __init__(self) -> None:
        self._consumers: list[TelemetryConsumer] = []

    def register(
        self,
        consumer: TelemetryConsumer,
    ) -> None:
        """
        Register a telemetry consumer.
        """

        if consumer not in self._consumers:
            self._consumers.append(consumer)

    def unregister(
        self,
        consumer: TelemetryConsumer,
    ) -> None:
        """
        Remove a telemetry consumer.
        """

        if consumer in self._consumers:
            self._consumers.remove(consumer)

    def publish(
        self,
        sample: TelemetrySample,
    ) -> None:
        """
        Publish one telemetry sample to all registered consumers.
        """

        for consumer in self._consumers:
            consumer.consume(sample)

    @property
    def consumer_count(self) -> int:
        """
        Number of currently registered consumers.
        """

        return len(self._consumers)