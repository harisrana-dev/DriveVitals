"""Shared exception hierarchy for the DriveVitals Digital Twin.

All Digital Twin components raise exceptions from this module rather than
built-in exceptions, so callers can catch failures at the appropriate
level of granularity (simulation-wide vs. manager-specific vs. entity
lookup failures).
"""

from __future__ import annotations


class DigitalTwinError(Exception):
    """Base class for all Digital Twin errors."""


class SimulationStateError(DigitalTwinError):
    """Raised when an operation is invalid for the current simulation state.

    Example: attempting to advance a tick while the simulation is paused,
    or starting a simulation that is already running.
    """


class ManagerError(DigitalTwinError):
    """Base class for errors raised by a manager module."""


class EntityNotFoundError(ManagerError):
    """Raised when a registry lookup fails for a given entity id."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """Initialize the error.

        Args:
            entity_type: Human-readable entity type, e.g. "Vehicle".
            entity_id: The id that could not be found.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' was not found.")


class EntityAlreadyExistsError(ManagerError):
    """Raised when attempting to register an entity id that already exists."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        """Initialize the error.

        Args:
            entity_type: Human-readable entity type, e.g. "Vehicle".
            entity_id: The id that already exists in the registry.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' already exists.")


class AssignmentError(ManagerError):
    """Raised when a dispatch/assignment operation cannot be completed."""


class ConfigurationError(DigitalTwinError):
    """Raised when a component receives invalid or missing configuration."""