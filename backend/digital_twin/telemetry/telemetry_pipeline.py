"""TelemetryPipeline: processes a TelemetryPacket through ordered stages.

Deliberately minimal for this sprint: one built-in validation stage,
plus an extensible stage list any future sprint can append to without
rewriting the pipeline itself. No analytics, no persistence, no
networking -- those are explicitly out of scope per the brief.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from digital_twin.common.exceptions import ConfigurationError
from digital_twin.telemetry.telemetry_packet import TelemetryPacket
from digital_twin.telemetry.telemetry_stream import TelemetryStream


@runtime_checkable
class TelemetryPipelineStage(Protocol):
    """Contract for a single telemetry processing stage.

    A stage receives a packet and returns a packet. Since
    `TelemetryPacket` is frozen, a stage that needs to change anything
    must return a *new* packet (e.g. via `dataclasses.replace`) rather
    than mutate the one it received -- satisfying "pipeline stages must
    not mutate packets in place." A stage that only validates or
    inspects simply returns its input unchanged.
    """

    def process(self, packet: TelemetryPacket) -> TelemetryPacket:
        """Process a packet, returning the (possibly new) result.

        Args:
            packet: The packet to process. Never mutated in place.

        Returns:
            The resulting packet -- `packet` itself if this stage made
            no changes, or a new `TelemetryPacket` otherwise.
        """
        ...


class TelemetryValidationStage:
    """Validates structural integrity of a packet, unchanged otherwise.

    Re-checks the same invariants `TelemetryPacket.__post_init__`
    already enforces at construction time. Since packets are immutable
    once built, this is somewhat redundant for packets built through
    `TelemetryGenerator` -- but the pipeline is a general-purpose entry
    point that may one day receive packets from other sources (e.g.
    deserialized from a future storage adapter), so validating here
    too is a deliberate defense-in-depth choice, not dead code.
    """

    def process(self, packet: TelemetryPacket) -> TelemetryPacket:
        """Validate the packet's required fields; pass it through unchanged.

        Args:
            packet: The packet to validate.

        Returns:
            `packet`, unchanged.

        Raises:
            ConfigurationError: If any required field is missing or
                invalid (empty vehicle_id, negative tick_id/sequence
                number, or no sensor readings).
        """
        if not packet.vehicle_id:
            raise ConfigurationError("TelemetryPacket.vehicle_id cannot be empty.")
        if packet.tick_id < 0:
            raise ConfigurationError("TelemetryPacket.tick_id cannot be negative.")
        if packet.sequence_number < 0:
            raise ConfigurationError("TelemetryPacket.sequence_number cannot be negative.")
        if not packet.sensor_readings:
            raise ConfigurationError("TelemetryPacket.sensor_readings cannot be empty.")
        return packet


class TelemetryPipeline:
    """Runs a TelemetryPacket through ordered stages, then forwards it.

    Depends only on the `TelemetryStream` Protocol for its output, and
    only on `TelemetryPipelineStage` for its processing steps -- both
    injected, so the pipeline is testable with fakes and extensible
    without modification (Open/Closed).
    """

    def __init__(
        self,
        stream: TelemetryStream,
        stages: Sequence[TelemetryPipelineStage] | None = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            stream: The TelemetryStream this pipeline forwards
                processed packets to.
            stages: Ordered processing stages to run before forwarding.
                Defaults to a single `TelemetryValidationStage`. Passed
                as a sequence and copied internally so the caller's
                original list can't be mutated to affect this pipeline
                after construction.
        """
        self._stream = stream
        self._stages: list[TelemetryPipelineStage] = (
            list(stages) if stages is not None else [TelemetryValidationStage()]
        )

    def add_stage(self, stage: TelemetryPipelineStage) -> None:
        """Append a processing stage to the end of the pipeline.

        Args:
            stage: The stage to add. Runs after all previously added
                stages, on every subsequent call to `process`.
        """
        self._stages.append(stage)

    def process(self, packet: TelemetryPacket) -> TelemetryPacket:
        """Run a packet through every stage, then publish it to the stream.

        Args:
            packet: The TelemetryPacket to process.

        Returns:
            The final packet after all stages have run (identical to
            the input packet unless a stage returned a new one) -- this
            is also the exact packet instance forwarded to the stream.
        """
        current = packet
        for stage in self._stages:
            current = stage.process(current)
        self._stream.publish(current)
        return current