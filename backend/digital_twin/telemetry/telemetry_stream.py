"""TelemetryStream: destination abstraction for processed TelemetryPackets.

Defines the `TelemetryStream` Protocol (so the Digital Twin depends
only on this abstraction) and `InMemoryTelemetryStream`, the concrete
implementation used for simulation. Neither type knows about
PostgreSQL, FastAPI, WebSockets, Redis, or Kafka -- those become future
adapters that implement this same Protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from digital_twin.telemetry.telemetry_packet import TelemetryPacket


@runtime_checkable
class TelemetryStream(Protocol):
    """Contract for anything TelemetryPackets can be routed to.

    A future PostgreSQL writer, WebSocket broadcaster, or Kafka
    producer implements this same Protocol; the Digital Twin's
    `TelemetryPipeline` depends only on this interface, never on a
    concrete transport.
    """

    def publish(self, packet: TelemetryPacket) -> None:
        """Publish a packet to this stream.

        Args:
            packet: The TelemetryPacket to publish.
        """
        ...

    def recent(self, limit: int | None = None) -> tuple[TelemetryPacket, ...]:
        """Return recently published packets, most-recent-last.

        Args:
            limit: If given, return at most this many of the most
                recently published packets. If `None`, return the
                full retained history.

        Returns:
            A tuple of packets. Always a fresh tuple, never a
            reference to any internal collection -- callers cannot
            mutate the stream's stored history through the return
            value.
        """
        ...


class InMemoryTelemetryStream:
    """An in-memory TelemetryStream suitable for simulation.

    Retains every published packet for inspection (`recent`) and
    additionally supports a separate, non-destructive FIFO cursor
    (`consume`) for callers that want to drain packets one at a time
    without losing the ability to inspect full history via `recent`.
    """

    def __init__(self) -> None:
        """Initialize an empty stream."""
        self._packets: list[TelemetryPacket] = []
        self._next_consume_index: int = 0

    def publish(self, packet: TelemetryPacket) -> None:
        """Publish a packet to this stream.

        Args:
            packet: The TelemetryPacket to publish. `TelemetryPacket`
                is itself immutable, so storing the reference directly
                cannot expose the stream to external mutation of the
                packet's fields.
        """
        self._packets.append(packet)

    def consume(self) -> TelemetryPacket | None:
        """Return the next not-yet-consumed packet, advancing the cursor.

        Non-destructive with respect to `recent()`: consumed packets
        remain visible there, since they're never removed from
        internal storage -- only the separate consume cursor advances.

        Returns:
            The next packet in publish order, or `None` if every
            published packet has already been consumed.
        """
        if self._next_consume_index >= len(self._packets):
            return None
        packet = self._packets[self._next_consume_index]
        self._next_consume_index += 1
        return packet

    def recent(self, limit: int | None = None) -> tuple[TelemetryPacket, ...]:
        """Return recently published packets, most-recent-last.

        Args:
            limit: If given, return at most this many of the most
                recently published packets. If `None`, return the
                full retained history.

        Returns:
            A fresh tuple copy; never a reference to the stream's
            internal list, so callers cannot mutate stored history.
        """
        if limit is None:
            return tuple(self._packets)
        return tuple(self._packets[-limit:])

    def __len__(self) -> int:
        """Return the total number of packets ever published."""
        return len(self._packets)