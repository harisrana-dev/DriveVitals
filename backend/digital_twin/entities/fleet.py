"""Fleet entity: the aggregate root representing an entire fleet company.

Per the Digital Twin philosophy, the simulation unit is the Fleet, not
an individual vehicle. This module models that aggregate as pure data
plus collection-management methods (register/find/start/complete). It
performs no physics, no scheduling policy, and no analytics -- those
remain the responsibility of Managers, Physics, and Analytics in other
sprints. `FleetManager` (Sprint 1) is the runtime-facing coordinator;
`Fleet` (this module) is the domain aggregate a future integration
sprint will have `FleetManager` operate on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from digital_twin.common.enums import MaintenanceStatus, TripStatus
from digital_twin.common.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from digital_twin.entities.driver import Driver
from digital_twin.entities.trip import Trip
from digital_twin.entities.vehicle import Vehicle


@dataclass
class MaintenanceRecord:
    """A single maintenance event recorded against a vehicle.

    Attributes:
        record_id: Unique identifier for this maintenance record.
        vehicle_id: Id of the vehicle this record applies to.
        status: Maintenance status this record represents.
        recorded_at: Simulated time the record was created.
        notes: Free-form notes about the maintenance event.
    """

    record_id: str
    vehicle_id: str
    status: MaintenanceStatus
    recorded_at: datetime
    notes: str = ""


@dataclass
class DispatchRecord:
    """A single dispatch decision recorded for the fleet's history.

    Attributes:
        record_id: Unique identifier for this dispatch record.
        trip_id: Id of the trip that was dispatched.
        driver_id: Id of the driver assigned.
        vehicle_id: Id of the vehicle assigned.
        dispatched_at: Simulated time the dispatch occurred.
    """

    record_id: str
    trip_id: str
    driver_id: str
    vehicle_id: str
    dispatched_at: datetime


@dataclass
class FleetStatistics:
    """Aggregate, fleet-wide counters.

    These are plain counters maintained alongside collection-management
    operations (e.g. incremented when a trip completes); no analytics
    or scoring is computed here.

    Attributes:
        total_vehicles: Count of vehicles ever registered.
        total_drivers: Count of drivers ever registered.
        total_trips_started: Count of trips ever started.
        total_trips_completed: Count of trips that reached COMPLETED.
        total_trips_cancelled: Count of trips that reached CANCELLED.
        total_distance_km: Sum of `distance_completed_km` across all
            completed trips.
    """

    total_vehicles: int = 0
    total_drivers: int = 0
    total_trips_started: int = 0
    total_trips_completed: int = 0
    total_trips_cancelled: int = 0
    total_distance_km: float = 0.0


@dataclass
class Fleet:
    """Aggregate root representing an entire fleet company.

    Owns the fleet's vehicles, drivers, and trips (both active and
    historical), plus maintenance and dispatch records and fleet-wide
    statistics. Methods here perform only collection management --
    registration, lookup, and trip lifecycle bookkeeping -- never
    physics, scheduling policy, or scoring.

    Attributes:
        fleet_id: Unique identifier for the fleet.
        fleet_name: Display name of the fleet company.
        vehicles: All registered vehicles, keyed by vehicle_id.
        drivers: All registered drivers, keyed by driver_id.
        trips: All trips ever created, keyed by trip_id (active and
            historical; trips are never removed from this mapping).
        active_trip_ids: Ids of trips currently in a non-terminal
            status.
        completed_trip_ids: Ids of trips that have reached a terminal
            status (COMPLETED or CANCELLED).
        maintenance_records: Maintenance history, keyed by record_id.
        dispatch_records: Chronological log of dispatch decisions.
        statistics: Aggregate fleet-wide counters.
    """

    fleet_id: str
    fleet_name: str
    vehicles: dict[str, Vehicle] = field(default_factory=dict)
    drivers: dict[str, Driver] = field(default_factory=dict)
    trips: dict[str, Trip] = field(default_factory=dict)
    active_trip_ids: set[str] = field(default_factory=set)
    completed_trip_ids: set[str] = field(default_factory=set)
    maintenance_records: dict[str, MaintenanceRecord] = field(default_factory=dict)
    dispatch_records: list[DispatchRecord] = field(default_factory=list)
    statistics: FleetStatistics = field(default_factory=FleetStatistics)

    # -- Vehicles ---------------------------------------------------------

    def register_vehicle(self, vehicle: Vehicle) -> Vehicle:
        """Register a new vehicle with the fleet.

        Args:
            vehicle: The Vehicle instance to register.

        Returns:
            The registered Vehicle.

        Raises:
            EntityAlreadyExistsError: If a vehicle with the same
                vehicle_id is already registered.
        """
        if vehicle.vehicle_id in self.vehicles:
            raise EntityAlreadyExistsError("Vehicle", vehicle.vehicle_id)
        self.vehicles[vehicle.vehicle_id] = vehicle
        self.statistics.total_vehicles += 1
        return vehicle

    def find_vehicle(self, vehicle_id: str) -> Vehicle:
        """Look up a registered vehicle by id.

        Args:
            vehicle_id: Id of the vehicle to retrieve.

        Returns:
            The matching Vehicle.

        Raises:
            EntityNotFoundError: If vehicle_id is not registered.
        """
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is None:
            raise EntityNotFoundError("Vehicle", vehicle_id)
        return vehicle

    # -- Drivers ------------------------------------------------------------

    def register_driver(self, driver: Driver) -> Driver:
        """Register a new driver with the fleet.

        Args:
            driver: The Driver instance to register.

        Returns:
            The registered Driver.

        Raises:
            EntityAlreadyExistsError: If a driver with the same
                driver_id is already registered.
        """
        if driver.driver_id in self.drivers:
            raise EntityAlreadyExistsError("Driver", driver.driver_id)
        self.drivers[driver.driver_id] = driver
        self.statistics.total_drivers += 1
        return driver

    def find_driver(self, driver_id: str) -> Driver:
        """Look up a registered driver by id.

        Args:
            driver_id: Id of the driver to retrieve.

        Returns:
            The matching Driver.

        Raises:
            EntityNotFoundError: If driver_id is not registered.
        """
        driver = self.drivers.get(driver_id)
        if driver is None:
            raise EntityNotFoundError("Driver", driver_id)
        return driver

    # -- Trips ------------------------------------------------------------

    def register_trip(self, trip: Trip) -> Trip:
        """Register a newly created trip with the fleet, as active.

        Args:
            trip: The Trip instance to register.

        Returns:
            The registered Trip.

        Raises:
            EntityAlreadyExistsError: If a trip with the same trip_id
                is already registered.
        """
        if trip.trip_id in self.trips:
            raise EntityAlreadyExistsError("Trip", trip.trip_id)
        self.trips[trip.trip_id] = trip
        self.active_trip_ids.add(trip.trip_id)
        return trip

    def find_trip(self, trip_id: str) -> Trip:
        """Look up a trip by id, whether active or historical.

        Args:
            trip_id: Id of the trip to retrieve.

        Returns:
            The matching Trip.

        Raises:
            EntityNotFoundError: If trip_id is not registered.
        """
        trip = self.trips.get(trip_id)
        if trip is None:
            raise EntityNotFoundError("Trip", trip_id)
        return trip

    def start_trip(self, trip_id: str, started_at: datetime) -> Trip:
        """Mark a registered trip as started.

        Args:
            trip_id: Id of the trip to start.
            started_at: Simulated time the trip started.

        Returns:
            The updated Trip.

        Raises:
            EntityNotFoundError: If trip_id is not registered.
        """
        trip = self.find_trip(trip_id)
        trip.start_time = started_at
        trip.status = TripStatus.IN_PROGRESS
        self.statistics.total_trips_started += 1
        return trip

    def complete_trip(self, trip_id: str, ended_at: datetime, cancelled: bool = False) -> Trip:
        """Mark a trip as finished, moving it into the historical set.

        The trip remains in `self.trips` permanently; only its status
        and the active/completed id sets change. Completed trips are
        never deleted.

        Args:
            trip_id: Id of the trip to complete.
            ended_at: Simulated time the trip ended.
            cancelled: If True, marks the trip CANCELLED instead of
                COMPLETED.

        Returns:
            The finalized Trip.

        Raises:
            EntityNotFoundError: If trip_id is not registered.
        """
        trip = self.find_trip(trip_id)
        trip.end_time = ended_at
        trip.status = TripStatus.CANCELLED if cancelled else TripStatus.COMPLETED

        self.active_trip_ids.discard(trip_id)
        self.completed_trip_ids.add(trip_id)

        if cancelled:
            self.statistics.total_trips_cancelled += 1
        else:
            self.statistics.total_trips_completed += 1
            self.statistics.total_distance_km += trip.distance_completed_km

        return trip

    # -- Maintenance & dispatch history ---------------------------------

    def record_maintenance(self, record: MaintenanceRecord) -> MaintenanceRecord:
        """Add a maintenance record to the fleet's history.

        Args:
            record: The MaintenanceRecord to add.

        Returns:
            The added MaintenanceRecord.

        Raises:
            EntityAlreadyExistsError: If a record with the same
                record_id already exists.
        """
        if record.record_id in self.maintenance_records:
            raise EntityAlreadyExistsError("MaintenanceRecord", record.record_id)
        self.maintenance_records[record.record_id] = record
        return record

    def record_dispatch(self, record: DispatchRecord) -> DispatchRecord:
        """Append a dispatch record to the fleet's dispatch history.

        Args:
            record: The DispatchRecord to append.

        Returns:
            The appended DispatchRecord.
        """
        self.dispatch_records.append(record)
        return record

    # -- Convenience views --------------------------------------------------

    def list_active_trips(self) -> list[Trip]:
        """List all currently active (non-terminal) trips.

        Returns:
            Trip instances whose ids are in `active_trip_ids`.
        """
        return [self.trips[trip_id] for trip_id in self.active_trip_ids]

    def list_completed_trips(self) -> list[Trip]:
        """List all trips that have reached a terminal status.

        Returns:
            Trip instances whose ids are in `completed_trip_ids`.
        """
        return [self.trips[trip_id] for trip_id in self.completed_trip_ids]