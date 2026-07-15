"""
DriveVitals Driver Model

Represents a fleet driver.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins.timestamp import TimestampMixin


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    # -----------------------------------
    # Primary Key
    # -----------------------------------

    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -----------------------------------
    # Foreign Key
    # -----------------------------------

    fleet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fleets.fleet_id"),
        nullable=False,
    )

    # -----------------------------------
    # Driver Information
    # -----------------------------------

    employee_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    license_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    # -----------------------------------
    # Relationships
    # -----------------------------------

    fleet: Mapped["Fleet"] = relationship(
        back_populates="drivers",
    )

    trips: Mapped[list["Trip"]] = relationship(
        back_populates="driver",
        cascade="all, delete-orphan",
    )

    # -----------------------------------
    # String Representation
    # -----------------------------------

    def __repr__(self) -> str:
        return (
            f"<Driver("
            f"{self.employee_id}, "
            f"{self.full_name})>"
        )