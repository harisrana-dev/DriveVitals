"""MaintenanceManager: tracks scheduled maintenance and inspection state.

Sprint 1 scope: registry and status tracking only, driven by simple
mileage/date thresholds from configuration. Actual wear calculation
(from driving conditions, physics, etc.) belongs to future sprints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from digital_twin.common.enums import ExecutionPhase, MaintenanceStatus
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.config.simulation_config import MaintenanceManagerConfig
from digital_twin.runtime.tick_context import TickContext

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceRecord:
    """Minimal, persistent maintenance record for a single vehicle.

    Attributes:
        vehicle_id: Id of the vehicle this record tracks.
        status: Current maintenance status.
        next_service_due_km: Odometer reading at which the next
            scheduled service is due.
        last_inspection_date: Simulated date of the most recent
            inspection.
        next_inspection_due_date: Simulated date the next inspection
            is due.
    """

    vehicle_id: str
    status: MaintenanceStatus = MaintenanceStatus.OK
    next_service_due_km: float = 10_000.0
    last_inspection_date: datetime | None = None
    next_inspection_due_date: datetime | None = None


class MaintenanceManager:
    """Owns maintenance/inspection registry and status derivation."""

    def __init__(self, config: MaintenanceManagerConfig) -> None:
        """Initialize an empty maintenance registry.

        Args:
            config: Thresholds for due-soon mileage and inspection
                interval.
        """
        self._config = config
        self._records: dict[str, MaintenanceRecord] = {}

    @property
    def phase(self) -> ExecutionPhase:
        """ExecutionPhase: MaintenanceManager runs during the MAINTENANCE phase."""
        return ExecutionPhase.MAINTENANCE

    def register_vehicle(
        self,
        vehicle_id: str,
        inspection_date: datetime,
        next_service_due_km: float = 10_000.0,
    ) -> MaintenanceRecord:
        """Register maintenance tracking for a vehicle.

        Args:
            vehicle_id: Id of the vehicle to track.
            inspection_date: Simulated date of the vehicle's last
                inspection (or registration date, if new).
            next_service_due_km: Odometer reading at which the next
                scheduled service is due.

        Returns:
            The newly created MaintenanceRecord.

        Raises:
            EntityAlreadyExistsError: If vehicle_id is already tracked.
        """
        if vehicle_id in self._records:
            raise EntityAlreadyExistsError("MaintenanceRecord", vehicle_id)
        record = MaintenanceRecord(
            vehicle_id=vehicle_id,
            next_service_due_km=next_service_due_km,
            last_inspection_date=inspection_date,
            next_inspection_due_date=inspection_date
            + timedelta(days=self._config.inspection_interval_days),
        )
        self._records[vehicle_id] = record
        logger.info("Registered maintenance tracking for vehicle %s", vehicle_id)
        return record

    def get_record(self, vehicle_id: str) -> MaintenanceRecord:
        """Look up a vehicle's maintenance record.

        Args:
            vehicle_id: Id of the vehicle to retrieve.

        Returns:
            The matching MaintenanceRecord.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        return self._require(vehicle_id)

    def list_records(self) -> list[MaintenanceRecord]:
        """List all tracked maintenance records.

        Returns:
            All MaintenanceRecord instances currently tracked.
        """
        return list(self._records.values())

    def list_overdue(self) -> list[MaintenanceRecord]:
        """List vehicles whose maintenance status is OVERDUE.

        Returns:
            MaintenanceRecords with status OVERDUE.
        """
        return [r for r in self._records.values() if r.status == MaintenanceStatus.OVERDUE]

    def mark_in_progress(self, vehicle_id: str) -> None:
        """Mark a vehicle's maintenance as currently being performed.

        Args:
            vehicle_id: Id of the vehicle undergoing maintenance.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        record = self._require(vehicle_id)
        record.status = MaintenanceStatus.IN_PROGRESS

    def complete_service(
        self,
        vehicle_id: str,
        completed_at: datetime,
        current_odometer_km: float,
        service_interval_km: float,
    ) -> None:
        """Record completion of a scheduled service.

        Args:
            vehicle_id: Id of the serviced vehicle.
            completed_at: Simulated time service was completed.
            current_odometer_km: Vehicle's odometer at time of service.
            service_interval_km: Distance until the next service is due.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        record = self._require(vehicle_id)
        record.status = MaintenanceStatus.OK
        record.next_service_due_km = current_odometer_km + service_interval_km
        logger.info(
            "Vehicle %s service completed; next due at %.1f km",
            vehicle_id,
            record.next_service_due_km,
        )

    def complete_inspection(self, vehicle_id: str, inspected_at: datetime) -> None:
        """Record completion of a mandatory inspection.

        Args:
            vehicle_id: Id of the inspected vehicle.
            inspected_at: Simulated time the inspection was completed.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        record = self._require(vehicle_id)
        record.last_inspection_date = inspected_at
        record.next_inspection_due_date = inspected_at + timedelta(
            days=self._config.inspection_interval_days
        )
        logger.info("Vehicle %s inspection completed", vehicle_id)

    def evaluate_status(
        self,
        vehicle_id: str,
        current_odometer_km: float,
        current_time: datetime,
    ) -> MaintenanceStatus:
        """Recompute and store a vehicle's maintenance status.

        Status becomes OVERDUE if the odometer has passed the due
        mileage or the inspection due date has passed; DUE_SOON if
        within the configured mileage buffer; otherwise OK. A vehicle
        already IN_PROGRESS is left untouched.

        Args:
            vehicle_id: Id of the vehicle to evaluate.
            current_odometer_km: Vehicle's current odometer reading.
            current_time: Current simulated time.

        Returns:
            The (possibly updated) MaintenanceStatus.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        record = self._require(vehicle_id)
        if record.status == MaintenanceStatus.IN_PROGRESS:
            return record.status

        inspection_overdue = (
            record.next_inspection_due_date is not None
            and current_time >= record.next_inspection_due_date
        )
        mileage_overdue = current_odometer_km >= record.next_service_due_km
        mileage_due_soon = (
            record.next_service_due_km - current_odometer_km
            <= self._config.due_soon_mileage_threshold_km
        )

        if inspection_overdue or mileage_overdue:
            record.status = MaintenanceStatus.OVERDUE
        elif mileage_due_soon:
            record.status = MaintenanceStatus.DUE_SOON
        else:
            record.status = MaintenanceStatus.OK

        return record.status

    def on_tick(self, context: TickContext) -> None:
        """Per-tick hook for MaintenanceManager.

        Sprint 1 does not have odometer/wear data flowing in yet (that
        arrives from VehicleManager/Physics in later sprints), so this
        hook is a no-op placeholder that satisfies the TickableManager
        protocol. Once odometer data is available, this should call
        `evaluate_status` for every tracked vehicle.

        Args:
            context: The current tick's immutable context.
        """
        logger.debug("MaintenanceManager on_tick tick_id=%s (no-op)", context.tick_id)

    def _require(self, vehicle_id: str) -> MaintenanceRecord:
        """Look up a maintenance record or raise if it doesn't exist.

        Args:
            vehicle_id: Id to look up.

        Returns:
            The matching MaintenanceRecord.

        Raises:
            EntityNotFoundError: If vehicle_id is not tracked.
        """
        record = self._records.get(vehicle_id)
        if record is None:
            raise EntityNotFoundError("MaintenanceRecord", vehicle_id)
        return record