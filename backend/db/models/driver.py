from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    driver_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    license_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    employment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )
    behavior_profile: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard"
    )

    trips = relationship("Trip", back_populates="driver")
    behaviour_events = relationship("BehaviourEvent", back_populates="driver")
    alerts = relationship("Alert", back_populates="driver")
    driver_statistics = relationship(
        "DriverStatistics", back_populates="driver", uselist=False
    )
