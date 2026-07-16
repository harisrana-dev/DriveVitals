"""
DriveVitals Vehicle Model

Represents a vehicle that belongs to a fleet.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins.timestamp import TimestampMixin


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    # -----------------------------------
    # Primary Key
    # -----------------------------------

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -----------------------------------
    # Foreign Keys
    # -----------------------------------

    fleet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fleets.fleet_id"),
        nullable=False,
    )

    # -----------------------------------
    # Vehicle Information
    # -----------------------------------

    registration_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    manufacturer: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    vin: Mapped[str] = mapped_column(
        String(17),
        unique=True,
        nullable=False,
    )

    # -----------------------------------
    # Relationships
    # -----------------------------------

    fleet: Mapped["Fleet"] = relationship(
        back_populates="vehicles",
    )

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    analytics_snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    # -----------------------------------
    # String Representation
    # -----------------------------------

    def __repr__(self) -> str:
        return (
            f"<Vehicle("
            f"{self.registration_number}, "
            f"{self.manufacturer} "
            f"{self.model})>"
        )