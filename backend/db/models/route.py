from uuid import uuid4

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Route(TimestampMixin, Base):
    __tablename__ = "routes"

    route_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    route_type: Mapped[str] = mapped_column(String(30), nullable=False)
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_distance_km: Mapped[float] = mapped_column(Float, nullable=False)

    trips = relationship("Trip", back_populates="route")
