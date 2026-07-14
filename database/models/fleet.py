"""
DriveVitals Fleet Model

Represents a fleet (company or organization) that owns
multiple vehicles and employs multiple drivers.
"""

from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.mixins.timestamp import TimestampMixin


class Fleet(TimestampMixin, Base):
    __tablename__ = "fleets"

    # -----------------------------------
    # Primary Key
    # -----------------------------------

    fleet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -----------------------------------
    # Fleet Information
    # -----------------------------------

    fleet_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    # -----------------------------------
    # Relationships
    # -----------------------------------

    vehicles: Mapped[List["Vehicle"]] = relationship(
        back_populates="fleet",
        cascade="all, delete-orphan",
    )

    drivers: Mapped[List["Driver"]] = relationship(
        back_populates="fleet",
        cascade="all, delete-orphan",
    )

    # -----------------------------------
    # String Representation
    # -----------------------------------

    def __repr__(self) -> str:
        return f"<Fleet(name='{self.fleet_name}')>"