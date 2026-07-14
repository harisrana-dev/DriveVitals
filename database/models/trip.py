"""
DriveVitals Trip Model

Represents one complete driving session.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    ForeignKey,
    Float,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins.timestamp import TimestampMixin


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    # -----------------------------------
    # Primary Key
    # -----------------------------------

    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -----------------------------------
    # Foreign Keys
    # -----------------------------------

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
    )

    driver_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drivers.driver_id"),
        nullable=False,
    )

    # -----------------------------------
    # Trip Information
    # -----------------------------------

    start_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_time: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    trip_status: Mapped[str] = mapped_column(
        String(20),
        default="running",
    )

    # -----------------------------------
    # Distance Information
    # -----------------------------------

    start_odometer_km: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    end_odometer_km: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    distance_travelled_km: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # -----------------------------------
    # Trip Summary
    # -----------------------------------

    average_speed_kmh: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    maximum_speed_kmh: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    fuel_consumed_liters: Mapped[float] = mapped_column(
        Float,
        default=0,
    )

    trip_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    eco_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    safety_score: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    # -----------------------------------
    # Relationships
    # -----------------------------------

    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="trips",
    )

    driver: Mapped["Driver"] = relationship(
        back_populates="trips",
    )

    telemetry_records: Mapped[list["Telemetry"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )

    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
    )

    alerts: Mapped[list["Alert"]] = relationship(
       back_populates="trip",
       cascade="all, delete-orphan",
    )

    # -----------------------------------
    # String Representation
    # -----------------------------------

    def __repr__(self) -> str:
        return (
            f"<Trip("
            f"{self.trip_id}, "
            f"{self.trip_status})>"
        )