"""Sink interfaces for the simulation integration layer.

Defines clean adapter boundaries so database, WebSocket, and other
external consumers can subscribe to simulation output without
modifying the Digital Twin core.

Usage:
    Implement a sink class that inherits from the relevant base.
    Pass it to SimulationRunner via the constructor.

    runner = SimulationRunner(
        telemetry_sinks=[MyDatabaseTelemetrySink()],
        analytics_sinks=[MyAnalyticsSink()],
        event_sinks=[MyEventSink()],
    )

The Digital Twin core (Vehicle, VehicleState, Physics, Sensors,
Telemetry, Analytics) remains untouched by sink implementations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from digital_twin.physics.physics_engine import PhysicsTickResult
from digital_twin.telemetry.telemetry_packet import TelemetryPacket

logger = logging.getLogger(__name__)


class TelemetrySink(ABC):
    """Receives TelemetryPacket from each vehicle on each tick.

    Implementations should persist or forward the packet to
    external systems (database, message queue, WebSocket, etc.).
    """

    @abstractmethod
    def receive(
        self,
        packet: TelemetryPacket,
        physics_result: PhysicsTickResult | None = None,
    ) -> None:
        """Process one telemetry packet.

        Args:
            packet: The immutable TelemetryPacket from the Digital Twin.
            physics_result: Optional physics metrics for this tick.
        """


class AnalyticsSink(ABC):
    """Receives analytics results from each vehicle on each tick.

    Implementations should persist or forward analytics output to
    external systems.
    """

    @abstractmethod
    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        analytics_result: dict,
    ) -> None:
        """Process one analytics result.

        Args:
            vehicle_id: Id of the vehicle.
            tick_id: Simulation tick.
            simulation_time: Simulated time.
            analytics_result: The full analytics output dict.
        """


class EventSink(ABC):
    """Receives analytics events from each vehicle on each tick.

    Implementations should persist or forward events to external
    systems. Events are extracted from the analytics result.
    """

    @abstractmethod
    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        events: list[dict],
    ) -> None:
        """Process analytics events for one vehicle on one tick.

        Args:
            vehicle_id: Id of the vehicle.
            tick_id: Simulation tick.
            simulation_time: Simulated time.
            events: List of event dicts from the analytics result.
        """


class LiveUpdateSink(ABC):
    """Receives live per-tick updates for frontend consumption.

    Implementations should forward structured updates to
    WebSocket clients or other live consumers.
    """

    @abstractmethod
    def receive(
        self,
        tick_id: int,
        simulation_time: datetime,
        vehicle_updates: list[dict],
    ) -> None:
        """Process a live update for one tick.

        Args:
            tick_id: Simulation tick.
            simulation_time: Simulated time.
            vehicle_updates: List of per-vehicle update dicts.
        """


# --- In-memory implementations for testing and development ---


class InMemoryTelemetrySink(TelemetrySink):
    """Stores telemetry packets in memory for testing."""

    def __init__(self) -> None:
        self._packets: list[TelemetryPacket] = []

    def receive(
        self,
        packet: TelemetryPacket,
        physics_result: PhysicsTickResult | None = None,
    ) -> None:
        self._packets.append(packet)

    @property
    def packets(self) -> list[TelemetryPacket]:
        return list(self._packets)

    @property
    def count(self) -> int:
        return len(self._packets)


class InMemoryAnalyticsSink(AnalyticsSink):
    """Stores analytics results in memory for testing."""

    def __init__(self) -> None:
        self._results: list[dict] = []

    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        analytics_result: dict,
    ) -> None:
        self._results.append({
            "vehicle_id": vehicle_id,
            "tick_id": tick_id,
            "simulation_time": simulation_time,
            "analytics_result": analytics_result,
        })

    @property
    def results(self) -> list[dict]:
        return list(self._results)

    @property
    def count(self) -> int:
        return len(self._results)


class InMemoryEventSink(EventSink):
    """Stores events in memory for testing."""

    def __init__(self) -> None:
        self._events: list[dict] = []

    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        events: list[dict],
    ) -> None:
        for event in events:
            self._events.append({
                "vehicle_id": vehicle_id,
                "tick_id": tick_id,
                "simulation_time": simulation_time,
                "event": event,
            })

    @property
    def events(self) -> list[dict]:
        return list(self._events)

    @property
    def count(self) -> int:
        return len(self._events)


class InMemoryLiveUpdateSink(LiveUpdateSink):
    """Stores live updates in memory for testing."""

    def __init__(self) -> None:
        self._updates: list[dict] = []

    def receive(
        self,
        tick_id: int,
        simulation_time: datetime,
        vehicle_updates: list[dict],
    ) -> None:
        self._updates.append({
            "tick_id": tick_id,
            "simulation_time": simulation_time,
            "vehicle_updates": vehicle_updates,
        })

    @property
    def updates(self) -> list[dict]:
        return list(self._updates)

    @property
    def count(self) -> int:
        return len(self._updates)


class LoggingTelemetrySink(TelemetrySink):
    """Logs telemetry packets to the standard logger."""

    def receive(
        self,
        packet: TelemetryPacket,
        physics_result: PhysicsTickResult | None = None,
    ) -> None:
        logger.info(
            "TELEMETRY | vehicle=%s tick=%d seq=%d readings=%d",
            packet.vehicle_id,
            packet.tick_id,
            packet.sequence_number,
            len(packet.sensor_readings),
        )


class LoggingAnalyticsSink(AnalyticsSink):
    """Logs analytics results to the standard logger."""

    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        analytics_result: dict,
    ) -> None:
        events = analytics_result.get("events", [])
        if events:
            logger.info(
                "ANALYTICS | vehicle=%s tick=%d events=%d",
                vehicle_id,
                tick_id,
                len(events),
            )


class LoggingEventSink(EventSink):
    """Logs events to the standard logger."""

    def receive(
        self,
        vehicle_id: str,
        tick_id: int,
        simulation_time: datetime,
        events: list[dict],
    ) -> None:
        for event in events:
            logger.info(
                "EVENT | vehicle=%s tick=%d event=%s severity=%s",
                vehicle_id,
                tick_id,
                event.get("event_type", "unknown"),
                event.get("severity", "unknown"),
            )
