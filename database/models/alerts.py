"""
DriveVitals Alert Model

Stores detected fleet events and warnings.

Alerts are generated from telemetry analysis,
vehicle health analysis, and fleet intelligence rules.
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



class Alert(TimestampMixin, Base):

    __tablename__ = "alerts"


    # =====================================================
    # Primary Key
    # =====================================================

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    # =====================================================
    # Foreign Keys
    # =====================================================

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
        index=True,
    )


    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("trips.trip_id"),
        nullable=True,
        index=True,
    )


    telemetry_id: Mapped[int | None] = mapped_column(
        ForeignKey("telemetry.telemetry_id"),
        nullable=True,
        index=True,
    )


    # =====================================================
    # Alert Information
    # =====================================================

    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )


    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
    )


    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


    # =====================================================
    # Status Tracking
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )


    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    # =====================================================
    # Relationships
    # =====================================================

    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="alerts"
    )


    trip: Mapped["Trip"] = relationship(
        back_populates="alerts"
    )


    telemetry: Mapped["Telemetry"] = relationship(
        back_populates="alerts"
    )


    def __repr__(self):

        return (
            f"<Alert("
            f"type={self.alert_type}, "
            f"severity={self.severity})>"
        )