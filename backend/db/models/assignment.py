from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Assignment(TimestampMixin, Base):
    """Connects a driver, a vehicle and a route for the digital twin lab.

    This is the persisted, admin-managed form of the runtime-only
    ``fleet.models.assignment.Assignment`` dataclass. It references
    persisted drivers, vehicles and routes directly.
    """

    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint(
            "driver_id",
            "vehicle_id",
            "route_id",
            name="uq_assignments_driver_vehicle_route",
        ),
    )

    assignment_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    driver_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drivers.driver_id"), nullable=False, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vehicles.vehicle_id"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("routes.route_id"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    driver = relationship("Driver")
    vehicle = relationship("Vehicle")
    route = relationship("Route")
    scenarios = relationship(
        "SimulationScenario",
        secondary="scenario_assignments",
        back_populates="assignments",
    )
