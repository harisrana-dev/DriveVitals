from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    driver_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("drivers.driver_id"), nullable=True
    )
    trip_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("trips.trip_id"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    condition: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    evidence: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="alert_engine"
    )

    vehicle = relationship("Vehicle", back_populates="alerts")
    driver = relationship("Driver", back_populates="alerts")
    trip = relationship("Trip", back_populates="alerts")
