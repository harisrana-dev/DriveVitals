from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class BehaviourEvent(Base):
    __tablename__ = "behaviour_events"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.trip_id"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    driver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drivers.driver_id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_value: Mapped[float] = mapped_column(Float, nullable=False)
    average_value: Mapped[float] = mapped_column(Float, nullable=False)

    trip = relationship("Trip", back_populates="behaviour_events")
    vehicle = relationship("Vehicle", back_populates="behaviour_events")
    driver = relationship("Driver", back_populates="behaviour_events")
