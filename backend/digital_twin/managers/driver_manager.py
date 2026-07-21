"""DriverManager: owns driver registry, availability, hours, fatigue, breaks.

Sprint 1 scope: tracks registry-level driver state (status, working
hours, fatigue flag, break scheduling) using simple accumulation rules
driven by configuration thresholds. It does NOT compute driver
behavior/decisions -- that belongs to the future `decision/` module.
"""

from __future__ import annotations

import logging

from digital_twin.common.enums import DriverStatus, ExecutionPhase
from digital_twin.common.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from digital_twin.config.simulation_config import DriverManagerConfig
from digital_twin.entities.driver import Driver
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


class DriverManager:
    """Owns the driver registry and its availability/fatigue bookkeeping."""

    def __init__(self, config: DriverManagerConfig) -> None:
        """Initialize an empty driver registry."""
        self._config = config
        self._drivers: dict[str, Driver] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: DriverManager runs during the DRIVERS phase."""
        return ExecutionPhase.DRIVERS

    def register_driver(self, driver: Driver) -> Driver:
        """Register a new driver entity."""
        if driver.driver_id in self._drivers:
            raise EntityAlreadyExistsError("Driver", driver.driver_id)

        self._drivers[driver.driver_id] = driver

        logger.info(
            "Registered driver %s (%s)",
            driver.driver_id,
            driver.name,
        )

        return driver

    def deregister_driver(self, driver_id: str) -> None:
        """Remove a driver from the registry permanently."""
        self._require(driver_id)
        del self._drivers[driver_id]

        logger.info("Deregistered driver %s", driver_id)

    def get_driver(self, driver_id: str) -> Driver:
        """Look up a driver by ID."""
        return self._require(driver_id)

    def list_drivers(self) -> list[Driver]:
        """List all registered drivers."""
        return list(self._drivers.values())

    def list_available_drivers(self) -> list[Driver]:
        """List drivers currently available for assignment."""
        return [
            driver
            for driver in self._drivers.values()
            if driver.status == DriverStatus.AVAILABLE
        ]

    def set_status(
        self,
        driver_id: str,
        status: DriverStatus,
    ) -> None:
        """Update a driver's availability status."""
        driver = self._require(driver_id)

        logger.debug(
            "Driver %s status %s -> %s",
            driver_id,
            driver.status,
            status,
        )

        driver.status = status

    def assign(
        self,
        driver_id: str,
        vehicle_id: str,
        trip_id: str,
    ) -> None:
        """Assign a driver to a vehicle and trip."""
        driver = self._require(driver_id)

        driver.current_vehicle_id = vehicle_id
        driver.current_trip_id = trip_id
        driver.status = DriverStatus.ASSIGNED

    def release(self, driver_id: str) -> None:
        """Clear a driver's assignment and return them to AVAILABLE.

        Fatigue and break state are intentionally preserved.
        """
        driver = self._require(driver_id)

        driver.current_vehicle_id = None
        driver.current_trip_id = None

        if driver.status != DriverStatus.FATIGUED:
            driver.status = DriverStatus.AVAILABLE

    def is_available(self, driver_id: str) -> bool:
        """Check whether a driver is currently available."""
        return self._require(driver_id).status == DriverStatus.AVAILABLE

    def on_tick(self, context: TickContext) -> None:
        """Accumulate working hours and apply fatigue/break rules."""
        hours_elapsed = context.delta_time / 3600.0
        minutes_elapsed = context.delta_time / 60.0

        for driver in self._drivers.values():

            if driver.status == DriverStatus.ON_BREAK:
                driver.break_remaining_minutes = max(
                    0.0,
                    driver.break_remaining_minutes - minutes_elapsed,
                )

                driver.break_time_minutes += minutes_elapsed

                if driver.break_remaining_minutes == 0.0:
                    driver.status = DriverStatus.AVAILABLE
                    driver.continuous_work_hours = 0.0

                    logger.info(
                        "Driver %s break complete",
                        driver.driver_id,
                    )

                continue

            if driver.status in (
                DriverStatus.ASSIGNED,
                DriverStatus.ON_TRIP,
                DriverStatus.FATIGUED,
            ):
                driver.continuous_work_hours += hours_elapsed
                driver.working_hours += hours_elapsed

                if (
                    driver.continuous_work_hours
                    >= self._config.max_working_hours_per_shift
                ):
                    driver.status = DriverStatus.ON_BREAK
                    driver.break_remaining_minutes = (
                        self._config.mandatory_break_minutes
                    )

                    logger.info(
                        "Driver %s forced onto mandatory break after %.2f hours",
                        driver.driver_id,
                        driver.continuous_work_hours,
                    )

                elif (
                    driver.continuous_work_hours
                    >= self._config.fatigue_threshold_hours
                ):
                    if driver.status != DriverStatus.FATIGUED:
                        logger.info(
                            "Driver %s flagged FATIGUED after %.2f hours",
                            driver.driver_id,
                            driver.continuous_work_hours,
                        )

                    driver.status = DriverStatus.FATIGUED

    def _require(self, driver_id: str) -> Driver:
        """Look up a driver or raise if it does not exist."""
        driver = self._drivers.get(driver_id)

        if driver is None:
            raise EntityNotFoundError("Driver", driver_id)

        return driver