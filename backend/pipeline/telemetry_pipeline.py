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

import asyncio
import logging

from typing import Protocol

from backend.telemetry.models.telemetry_sample import TelemetrySample


logger = logging.getLogger(__name__)


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

        Every consumer is isolated: if one consumer fails (a persistence
        write, a WebSocket/client, an analytics step), the failure is
        logged with the consumer and vehicle context and the remaining
        consumers still receive the sample. A single bad consumer must
        never stop telemetry generation or silently drop downstream
        consumers.
        """

        for consumer in self._consumers:
            try:
                consumer.consume(sample)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Telemetry consumer %s failed for vehicle=%s at %s",
                    consumer.__class__.__name__,
                    sample.vehicle_id,
                    sample.timestamp,
                )

    @property
    def consumer_count(self) -> int:
        """
        Number of currently registered consumers.
        """

        return len(self._consumers)