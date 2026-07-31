from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class VehicleStatistics(Base):
    __tablename__ = "vehicle_statistics"

    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), primary_key=True
    )
    trip_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_distance_km: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_runtime_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    fuel_consumed_liters: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    average_fuel_efficiency: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    lifetime_health_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=100.0
    )
    utilization_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    vehicle = relationship("Vehicle", back_populates="vehicle_statistics")
