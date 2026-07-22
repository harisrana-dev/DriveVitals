"""DrivingScenario: lightweight deterministic driving behavior.

Provides a simple state machine that transitions vehicles through
realistic driving states: IDLE → STARTING → ACCELERATING → CRUISING
→ DECELERATING → STOPPED → repeat.

Each vehicle gets an independent scenario instance with configurable
behavior parameters. The scenario is deterministic when seeded.

This module does NOT own vehicle state or physics — it only produces
DriverIntent-compatible values that the existing Decision/Controller
chain consumes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum, auto


class DrivingState(str, Enum):
    """Current driving state of a vehicle."""

    IDLE = "IDLE"
    STARTING = "STARTING"
    ACCELERATING = "ACCELERATING"
    CRUISING = "CRUISING"
    DECELERATING = "DECELERATING"
    STOPPED = "STOPPED"


@dataclass(frozen=True)
class DrivingCommand:
    """Output of a driving scenario tick.

    Attributes:
        target_speed_kmh: Desired speed for the vehicle.
        throttle: Throttle request (0.0 to 1.0).
        brake: Brake request (0.0 to 1.0).
        state: Current driving state.
        reason: Human-readable explanation.
    """

    target_speed_kmh: float
    throttle: float
    brake: float
    state: DrivingState
    reason: str


@dataclass
class DrivingScenario:
    """Deterministic driving scenario for a single vehicle.

    Transitions through driving states based on current speed and
    configurable thresholds. Each vehicle should have its own
    scenario instance with potentially different parameters.

    Attributes:
        vehicle_id: Id of the vehicle this scenario controls.
        max_speed_kmh: Target cruising speed.
        acceleration_rate: Speed increase per tick (km/h).
        deceleration_rate: Speed decrease per tick (km/h).
        idle_duration_ticks: Ticks to remain idle before starting.
        cruise_duration_ticks: Ticks to cruise before decelerating.
        stop_duration_ticks: Ticks to remain stopped before restarting.
    """

    vehicle_id: str
    max_speed_kmh: float = 60.0
    acceleration_rate: float = 5.0
    deceleration_rate: float = 8.0
    idle_duration_ticks: int = 3
    cruise_duration_ticks: int = 10
    stop_duration_ticks: int = 2

    # Internal state
    _state: DrivingState = DrivingState.IDLE
    _state_ticks: int = 0
    _current_speed: float = 0.0

    def tick(self, current_speed_kmh: float) -> DrivingCommand:
        """Advance the scenario by one tick.

        Args:
            current_speed_kmh: Current vehicle speed from physics.

        Returns:
            DrivingCommand with target speed, throttle, brake.
        """
        self._current_speed = current_speed_kmh
        self._state_ticks += 1

        if self._state == DrivingState.IDLE:
            return self._tick_idle()
        elif self._state == DrivingState.STARTING:
            return self._tick_starting()
        elif self._state == DrivingState.ACCELERATING:
            return self._tick_accelerating()
        elif self._state == DrivingState.CRUISING:
            return self._tick_cruising()
        elif self._state == DrivingState.DECELERATING:
            return self._tick_decelerating()
        elif self._state == DrivingState.STOPPED:
            return self._tick_stopped()
        else:
            return self._tick_idle()

    def _tick_idle(self) -> DrivingCommand:
        if self._state_ticks >= self.idle_duration_ticks:
            self._state = DrivingState.STARTING
            self._state_ticks = 0
            return DrivingCommand(
                target_speed_kmh=0.0,
                throttle=0.0,
                brake=0.0,
                state=DrivingState.STARTING,
                reason="Transitioning from idle to starting",
            )
        return DrivingCommand(
            target_speed_kmh=0.0,
            throttle=0.0,
            brake=1.0,
            state=DrivingState.IDLE,
            reason="Vehicle idling",
        )

    def _tick_starting(self) -> DrivingCommand:
        self._state = DrivingState.ACCELERATING
        self._state_ticks = 0
        return DrivingCommand(
            target_speed_kmh=self.max_speed_kmh,
            throttle=0.3,
            brake=0.0,
            state=DrivingState.ACCELERATING,
            reason="Starting to accelerate",
        )

    def _tick_accelerating(self) -> DrivingCommand:
        if self._current_speed >= self.max_speed_kmh * 0.95:
            self._state = DrivingState.CRUISING
            self._state_ticks = 0
            return DrivingCommand(
                target_speed_kmh=self.max_speed_kmh,
                throttle=0.2,
                brake=0.0,
                state=DrivingState.CRUISING,
                reason="Reached cruising speed",
            )
        # Progressive throttle based on how close to target
        ratio = self._current_speed / max(self.max_speed_kmh, 1.0)
        throttle = max(0.1, min(0.8, 0.8 - ratio * 0.6))
        return DrivingCommand(
            target_speed_kmh=self.max_speed_kmh,
            throttle=throttle,
            brake=0.0,
            state=DrivingState.ACCELERATING,
            reason=f"Accelerating at {self._current_speed:.1f} km/h",
        )

    def _tick_cruising(self) -> DrivingCommand:
        if self._state_ticks >= self.cruise_duration_ticks:
            self._state = DrivingState.DECELERATING
            self._state_ticks = 0
            return DrivingCommand(
                target_speed_kmh=0.0,
                throttle=0.0,
                brake=0.3,
                state=DrivingState.DECELERATING,
                reason="Cruise complete, beginning deceleration",
            )
        # Maintain speed with minor throttle adjustments
        speed_ratio = self._current_speed / max(self.max_speed_kmh, 1.0)
        if speed_ratio > 1.05:
            throttle = 0.0
            brake = 0.1
        elif speed_ratio < 0.95:
            throttle = 0.2
            brake = 0.0
        else:
            throttle = 0.15
            brake = 0.0
        return DrivingCommand(
            target_speed_kmh=self.max_speed_kmh,
            throttle=throttle,
            brake=brake,
            state=DrivingState.CRUISING,
            reason=f"Cruising at {self._current_speed:.1f} km/h",
        )

    def _tick_decelerating(self) -> DrivingCommand:
        if self._current_speed <= 1.0:
            self._state = DrivingState.STOPPED
            self._state_ticks = 0
            return DrivingCommand(
                target_speed_kmh=0.0,
                throttle=0.0,
                brake=1.0,
                state=DrivingState.STOPPED,
                reason="Vehicle stopped",
            )
        return DrivingCommand(
            target_speed_kmh=0.0,
            throttle=0.0,
            brake=0.5,
            state=DrivingState.DECELERATING,
            reason=f"Decelerating from {self._current_speed:.1f} km/h",
        )

    def _tick_stopped(self) -> DrivingCommand:
        if self._state_ticks >= self.stop_duration_ticks:
            self._state = DrivingState.STARTING
            self._state_ticks = 0
            return DrivingCommand(
                target_speed_kmh=self.max_speed_kmh,
                throttle=0.3,
                brake=0.0,
                state=DrivingState.STARTING,
                reason="Restarting after stop",
            )
        return DrivingCommand(
            target_speed_kmh=0.0,
            throttle=0.0,
            brake=1.0,
            state=DrivingState.STOPPED,
            reason="Vehicle stopped",
        )

    @property
    def state(self) -> DrivingState:
        return self._state


def create_scenario_for_vehicle(
    vehicle_id: str,
    seed: int = 0,
    index: int = 0,
) -> DrivingScenario:
    """Create a deterministic driving scenario for a vehicle.

    Uses the seed and index to produce varied but reproducible
    behavior across vehicles.

    Args:
        vehicle_id: Id of the vehicle.
        seed: Random seed for determinism.
        index: Vehicle index for variation.

    Returns:
        A configured DrivingScenario.
    """
    # Derive deterministic parameters from seed + index
    hash_input = f"{seed}:{index}".encode()
    hash_val = int(hashlib.md5(hash_input).hexdigest()[:8], 16)

    max_speed = 40.0 + (hash_val % 50)  # 40-90 km/h
    accel_rate = 3.0 + (hash_val % 5)  # 3-7 km/h per tick
    decel_rate = 5.0 + (hash_val % 6)  # 5-10 km/h per tick
    idle_ticks = 2 + (hash_val % 3)  # 2-4 ticks
    cruise_ticks = 8 + (hash_val % 7)  # 8-14 ticks
    stop_ticks = 1 + (hash_val % 3)  # 1-3 ticks

    return DrivingScenario(
        vehicle_id=vehicle_id,
        max_speed_kmh=float(max_speed),
        acceleration_rate=float(accel_rate),
        deceleration_rate=float(decel_rate),
        idle_duration_ticks=idle_ticks,
        cruise_duration_ticks=cruise_ticks,
        stop_duration_ticks=stop_ticks,
    )
