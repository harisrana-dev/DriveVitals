from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        Index(
            "ix_maintenance_records_vehicle_type",
            "vehicle_id",
            "maintenance_type",
        ),
    )

    maintenance_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    maintenance_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    due_odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    component: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    vehicle = relationship("Vehicle", back_populates="maintenance_records")
