from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class DriverStatistics(Base):
    __tablename__ = "driver_statistics"

    driver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drivers.driver_id"), primary_key=True
    )
    total_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_driving_time_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    average_trip_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fuel_efficiency: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    speeding_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    harsh_braking_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aggressive_throttle_events: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    high_rpm_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    aggression_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    efficiency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    driver = relationship("Driver", back_populates="driver_statistics")
