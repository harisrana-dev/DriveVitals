"""
DriveVitals Maintenance Event Model

Stores vehicle maintenance issues,
service recommendations, and repair history.
"""


from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Text,
)

from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.base import Base
from database.mixins.timestamp import TimestampMixin



class MaintenanceEvent(TimestampMixin, Base):

    __tablename__ = "maintenance_events"


    # =====================================================
    # Primary Key
    # =====================================================

    maintenance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    # =====================================================
    # Relationships
    # =====================================================

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
        index=True,
    )


    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trips.trip_id"),
        nullable=True,
    )


    # =====================================================
    # Maintenance Information
    # =====================================================

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    issue: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
    )


    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )


    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    # =====================================================
    # Relationships
    # =====================================================

    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="maintenance_events"
    )


    trip: Mapped["Trip"] = relationship(
        back_populates="maintenance_events"
    )


    def __repr__(self):

        return (
            f"<MaintenanceEvent("
            f"{self.category}, "
            f"{self.priority})>"
        )