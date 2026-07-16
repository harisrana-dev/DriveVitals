"""DriverManager: owns driver registry, availability, hours, fatigue, breaks.

Sprint 1 scope: tracks registry-level driver state (status, working
hours, fatigue flag, break scheduling) using simple accumulation rules
driven by configuration thresholds. It does NOT compute driver
behavior/decisions -- that belongs to the future `decision/` module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from digital_twin.common.enums import DriverStatus, ExecutionPhase
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.config.simulation_config import DriverManagerConfig
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


@dataclass
class DriverRecord:
    """Minimal, persistent registry record for a single driver.

    Attributes:
        driver_id: Unique identifier for the driver.
        name: Display name of the driver.
        status: Current availability status.
        assigned_vehicle_id: Id of the vehicle currently assigned, if any.
        assigned_trip_id: Id of the trip currently assigned, if any.
        continuous_work_hours: Hours worked continuously since the last
            break, persists across ticks.
        break_remaining_minutes: Minutes remaining in a mandatory break,
            0 if not currently on break.
    """

    driver_id: str
    name: str
    status: DriverStatus = DriverStatus.AVAILABLE
    assigned_vehicle_id: str | None = None
    assigned_trip_id: str | None = None
    continuous_work_hours: float = 0.0
    break_remaining_minutes: float = 0.0


class DriverManager:
    """Owns the driver registry and its availability/fatigue bookkeeping."""

    def __init__(self, config: DriverManagerConfig) -> None:
        """Initialize an empty driver registry.

        Args:
            config: Thresholds for working hours, breaks, and fatigue.
        """
        self._config = config
        self._drivers: dict[str, DriverRecord] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: DriverManager runs during the DRIVERS phase."""
        return ExecutionPhase.DRIVERS

    def register_driver(self, driver_id: str, name: str) -> DriverRecord:
        """Register a new driver.

        Args:
            driver_id: Unique id for the new driver.
            name: Display name of the driver.

        Returns:
            The newly created DriverRecord.

        Raises:
            EntityAlreadyExistsError: If driver_id is already registered.
        """
        if driver_id in self._drivers:
            raise EntityAlreadyExistsError("Driver", driver_id)
        record = DriverRecord(driver_id=driver_id, name=name)
        self._drivers[driver_id] = record
        logger.info("Registered driver %s (%s)", driver_id, name)
        return record

    def deregister_driver(self, driver_id: str) -> None:
        """Remove a driver from the registry permanently.

        Args:
            driver_id: Id of the driver to remove.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        self._require(driver_id)
        del self._drivers[driver_id]
        logger.info("Deregistered driver %s", driver_id)

    def get_driver(self, driver_id: str) -> DriverRecord:
        """Look up a driver by id.

        Args:
            driver_id: Id of the driver to retrieve.

        Returns:
            The matching DriverRecord.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        return self._require(driver_id)

    def list_drivers(self) -> list[DriverRecord]:
        """List all registered drivers.

        Returns:
            All DriverRecord instances currently in the registry.
        """
        return list(self._drivers.values())

    def list_available_drivers(self) -> list[DriverRecord]:
        """List drivers currently available for assignment.

        Returns:
            DriverRecords whose status is AVAILABLE.
        """
        return [d for d in self._drivers.values() if d.status == DriverStatus.AVAILABLE]

    def set_status(self, driver_id: str, status: DriverStatus) -> None:
        """Update a driver's availability status.

        Args:
            driver_id: Id of the driver to update.
            status: New status to set.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        record = self._require(driver_id)
        logger.debug("Driver %s status %s -> %s", driver_id, record.status, status)
        record.status = status

    def assign(self, driver_id: str, vehicle_id: str, trip_id: str) -> None:
        """Mark a driver as assigned to a vehicle and trip.

        Args:
            driver_id: Id of the driver being assigned.
            vehicle_id: Id of the vehicle they are assigned to.
            trip_id: Id of the trip they are assigned to.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        record = self._require(driver_id)
        record.assigned_vehicle_id = vehicle_id
        record.assigned_trip_id = trip_id
        record.status = DriverStatus.ASSIGNED

    def release(self, driver_id: str) -> None:
        """Clear a driver's assignment and return them to AVAILABLE.

        Does not clear fatigue/break state -- releasing an assignment
        is independent from the driver's need for rest.

        Args:
            driver_id: Id of the driver to release.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        record = self._require(driver_id)
        record.assigned_vehicle_id = None
        record.assigned_trip_id = None
        if record.status != DriverStatus.FATIGUED:
            record.status = DriverStatus.AVAILABLE

    def is_available(self, driver_id: str) -> bool:
        """Check whether a driver is currently available for assignment.

        Args:
            driver_id: Id of the driver to check.

        Returns:
            True if the driver's status is AVAILABLE.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        return self._require(driver_id).status == DriverStatus.AVAILABLE

    def on_tick(self, context: TickContext) -> None:
        """Accumulate working hours and apply fatigue/break rules.

        For every driver currently ON_TRIP or ASSIGNED, this adds the
        tick's elapsed time to their continuous work hours. Once hours
        exceed the configured fatigue threshold, the driver is flagged
        FATIGUED. Drivers on break count down their remaining break
        time and are returned to AVAILABLE once it elapses.

        Args:
            context: The current tick's immutable context.
        """
        hours_elapsed = context.delta_time / 3600.0
        minutes_elapsed = context.delta_time / 60.0

        for record in self._drivers.values():
            if record.status == DriverStatus.ON_BREAK:
                record.break_remaining_minutes = max(
                    0.0, record.break_remaining_minutes - minutes_elapsed
                )
                if record.break_remaining_minutes == 0.0:
                    record.status = DriverStatus.AVAILABLE
                    record.continuous_work_hours = 0.0
                    logger.info("Driver %s break complete", record.driver_id)
                continue

            if record.status in (
                DriverStatus.ASSIGNED,
                DriverStatus.ON_TRIP,
                DriverStatus.FATIGUED,
            ):
                record.continuous_work_hours += hours_elapsed

                if record.continuous_work_hours >= self._config.max_working_hours_per_shift:
                    record.status = DriverStatus.ON_BREAK
                    record.break_remaining_minutes = self._config.mandatory_break_minutes
                    logger.info(
                        "Driver %s forced onto mandatory break after %.2f hours",
                        record.driver_id,
                        record.continuous_work_hours,
                    )
                elif record.continuous_work_hours >= self._config.fatigue_threshold_hours:
                    if record.status != DriverStatus.FATIGUED:
                        logger.info(
                            "Driver %s flagged FATIGUED after %.2f hours",
                            record.driver_id,
                            record.continuous_work_hours,
                        )
                    record.status = DriverStatus.FATIGUED

    def _require(self, driver_id: str) -> DriverRecord:
        """Look up a driver or raise if it doesn't exist.

        Args:
            driver_id: Id to look up.

        Returns:
            The matching DriverRecord.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        record = self._drivers.get(driver_id)
        if record is None:
            raise EntityNotFoundError("Driver", driver_id)
        return record