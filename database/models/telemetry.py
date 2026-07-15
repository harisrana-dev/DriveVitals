"""
DriveVitals Telemetry Model

Stores raw telemetry packets collected from
the simulator or OBD-II adapter.

Telemetry contains ONLY raw measurements.

No analytics belong here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Boolean,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database.base import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    # =====================================================
    # Primary Key
    # =====================================================

    telemetry_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # =====================================================
    # Relationships
    # =====================================================

    trip_id: Mapped[str] = mapped_column(
        ForeignKey("trips.trip_id"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # Packet Information
    # =====================================================

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # =====================================================
    # Vehicle Motion
    # =====================================================

    speed_kmh: Mapped[float] = mapped_column(Float)

    acceleration_mps2: Mapped[float] = mapped_column(Float)

    heading_deg: Mapped[float] = mapped_column(Float)

    odometer_km: Mapped[float] = mapped_column(Float)

    # =====================================================
    # Engine
    # =====================================================

    rpm: Mapped[int] = mapped_column(Integer)

    engine_load_percent: Mapped[float] = mapped_column(Float)

    throttle_position_percent: Mapped[float] = mapped_column(Float)

    coolant_temperature_c: Mapped[float] = mapped_column(Float)

    oil_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    oil_pressure_kpa: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    intake_air_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    maf_gps: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    map_kpa: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Fuel System
    # =====================================================

    fuel_rate_lph: Mapped[float] = mapped_column(Float)

    fuel_level_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Transmission
    # =====================================================

    gear: Mapped[int] = mapped_column(Integer)

    transmission_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Driver Inputs
    # =====================================================

    accelerator_pedal_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    brake_pedal_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    steering_angle_deg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Braking System
    # =====================================================

    brake_pressure_bar: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    abs_active: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # =====================================================
    # Electrical System
    # =====================================================

    battery_voltage_v: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    alternator_voltage_v: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Environment
    # =====================================================

    ambient_temperature_c: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    weather_condition: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # =====================================================
    # GPS
    # =====================================================

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    altitude_m: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # =====================================================
    # Simulator Metadata
    # =====================================================

    driver_personality: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    road_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    traffic_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    vehicle_load_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    trip_phase: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # =====================================================
    # Relationships
    # =====================================================

    trip: Mapped["Trip"] = relationship(
        back_populates="telemetry_records",
    )

    analysis: Mapped["TelemetryAnalysis"] = relationship(
        back_populates="telemetry",
        uselist=False,
        cascade="all, delete-orphan",
    )

    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="telemetry",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Telemetry("
            f"id={self.telemetry_id}, "
            f"speed={self.speed_kmh}, "
            f"rpm={self.rpm})>"
        )