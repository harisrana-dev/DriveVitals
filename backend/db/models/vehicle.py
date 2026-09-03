from uuid import uuid4

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    registration_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    vin: Mapped[str] = mapped_column(
        String(17), unique=True, nullable=False, index=True
    )
    manufacturer: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Descriptive name shown in the digital twin lab. Optional; falls
    # back to "make model" when unset.
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Simulation characteristics. These are simulation inputs (not
    # analytics conclusions) that influence how the OBD generator varies
    # telemetry for this vehicle relative to a baseline.
    fuel_efficiency_factor: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )
    acceleration_response: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )
    tank_capacity_liters: Mapped[float] = mapped_column(
        Float, nullable=False, default=60.0
    )

    trips = relationship("Trip", back_populates="vehicle")
    telemetry_samples = relationship("TelemetrySample", back_populates="vehicle")
    behaviour_events = relationship("BehaviourEvent", back_populates="vehicle")
    alerts = relationship("Alert", back_populates="vehicle")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle")
    vehicle_health = relationship(
        "VehicleHealth", back_populates="vehicle", uselist=False
    )
    vehicle_statistics = relationship(
        "VehicleStatistics", back_populates="vehicle", uselist=False
    )
