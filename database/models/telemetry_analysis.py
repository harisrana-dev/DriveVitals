"""
DriveVitals Telemetry Analysis Model

Stores processed intelligence generated from
individual telemetry packets.

This table contains derived metrics only.

Examples:
- Fuel efficiency calculation
- Driving behaviour detection
- Engine stress estimation
- Anomaly detection scores

Raw measurements belong to Telemetry.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.base import Base


class TelemetryAnalysis(Base):

    __tablename__ = "telemetry_analysis"


    # =====================================================
    # Primary Key
    # =====================================================

    analysis_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )


    # =====================================================
    # Relationship
    # =====================================================

    telemetry_id: Mapped[int] = mapped_column(
        ForeignKey("telemetry.telemetry_id"),
        nullable=False,
        index=True,
    )


    # =====================================================
    # Analysis Timestamp
    # =====================================================

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )


    # =====================================================
    # Fuel Intelligence
    # =====================================================

    fuel_efficiency_kmpl: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    fuel_rating: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )


    # =====================================================
    # Driver Behaviour Analysis
    # =====================================================

    harsh_acceleration: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


    harsh_braking: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


    overspeeding: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


    driver_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    # =====================================================
    # Vehicle Health Analysis
    # =====================================================

    engine_stress_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    anomaly_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )


    health_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )


    # =====================================================
    # Relationship Back
    # =====================================================

    telemetry: Mapped["Telemetry"] = relationship(
        back_populates="analysis"
    )


    def __repr__(self) -> str:

        return (
            f"<TelemetryAnalysis("
            f"id={self.analysis_id}, "
            f"fuel={self.fuel_efficiency_kmpl}, "
            f"driver_score={self.driver_score})>"
        )