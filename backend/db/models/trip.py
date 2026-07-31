from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Trip(Base):
    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    driver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drivers.driver_id"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("routes.route_id"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_used_liters: Mapped[float | None] = mapped_column(Float, nullable=True)
    average_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    trip_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="assigned")

    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")
    route = relationship("Route", back_populates="trips")
    telemetry_samples = relationship("TelemetrySample", back_populates="trip")
    behaviour_events = relationship("BehaviourEvent", back_populates="trip")
    alerts = relationship("Alert", back_populates="trip")
