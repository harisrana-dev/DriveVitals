from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class VehicleHealth(Base):
    __tablename__ = "vehicle_health"

    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), primary_key=True
    )
    overall_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    brake_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    transmission_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    cooling_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_system_health: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    vehicle = relationship("Vehicle", back_populates="vehicle_health")
