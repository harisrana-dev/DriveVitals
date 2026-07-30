from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class VehicleHealth(Base):
    __tablename__ = "vehicle_health"

    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), primary_key=True
    )
    overall_health_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    engine_health: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    brake_health: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    transmission_health: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    cooling_health: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    fuel_system_health: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    vehicle = relationship("Vehicle", back_populates="vehicle_health")
