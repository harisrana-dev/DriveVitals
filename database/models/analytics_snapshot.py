"""
DriveVitals Analytics Snapshot Model

Stores aggregated intelligence for vehicles.

This table powers the dashboard.

It represents the current state of a vehicle,
not individual telemetry packets.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    String,
    JSON,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.base import Base


class AnalyticsSnapshot(Base):

    __tablename__ = "analytics_snapshots"


    # =====================================================
    # Primary Key
    # =====================================================

    snapshot_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )


    # =====================================================
    # Vehicle Relationship
    # =====================================================

    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
        index=True,
    )


    # =====================================================
    # Snapshot Time
    # =====================================================

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


    # =====================================================
    # Fuel Intelligence
    # =====================================================

    average_fuel_efficiency_kmpl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    fuel_trend: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


    # =====================================================
    # Driver Intelligence
    # =====================================================

    driver_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    driving_style: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )


    # =====================================================
    # Vehicle Health Intelligence
    # =====================================================

    health_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    health_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )


    maintenance_risk: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )


    # =====================================================
    # Fleet Intelligence
    # =====================================================

    risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


    insights: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )


    # =====================================================
    # Relationship
    # =====================================================

    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="analytics_snapshots"
    )


    def __repr__(self) -> str:

        return (
            f"<AnalyticsSnapshot("
            f"id={self.snapshot_id}, "
            f"vehicle={self.vehicle_id}, "
            f"health={self.health_score})>"
        )