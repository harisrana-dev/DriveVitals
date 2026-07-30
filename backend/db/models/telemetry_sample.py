from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    sample_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.trip_id"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    speed_kmh: Mapped[float] = mapped_column(Float, nullable=False)
    rpm: Mapped[float] = mapped_column(Float, nullable=False)
    engine_load_percent: Mapped[float] = mapped_column(Float, nullable=False)
    throttle_percent: Mapped[float] = mapped_column(Float, nullable=False)
    brake_percent: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_rate_lph: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_level_percent: Mapped[float] = mapped_column(Float, nullable=False)
    coolant_temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    odometer_km: Mapped[float] = mapped_column(Float, nullable=False)

    trip = relationship("Trip", back_populates="telemetry_samples")
    vehicle = relationship("Vehicle", back_populates="telemetry_samples")
