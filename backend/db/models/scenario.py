from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin

scenario_assignments = Table(
    "scenario_assignments",
    Base.metadata,
    Column(
        "scenario_id",
        String(36),
        ForeignKey("simulation_scenarios.scenario_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "assignment_id",
        String(36),
        ForeignKey("assignments.assignment_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class SimulationScenario(TimestampMixin, Base):
    """A deliberate digital twin experiment.

    A scenario describes the fleet (drivers, vehicles, routes,
    assignments) to simulate plus the simulation parameters. It is a
    configuration object — it does not itself run. Launching a scenario
    creates a SimulationRun.

    Lifecycle: draft -> ready -> running -> completed (or failed).
    """

    __tablename__ = "simulation_scenarios"

    scenario_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # Simulation parameters
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    simulation_speed: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    runs = relationship(
        "SimulationRun",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )

    # Assignments that compose this scenario's fleet.
    assignments = relationship(
        "Assignment",
        secondary=scenario_assignments,
        back_populates="scenarios",
    )


class SimulationRun(TimestampMixin, Base):
    """A single execution of a scenario.

    Tracks the lifecycle of one launched scenario: when it started, its
    seed, and its outcome counters. Historical telemetry and trips are
    produced through the normal simulation pipeline, not here.
    """

    __tablename__ = "simulation_runs"

    run_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    scenario_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("simulation_scenarios.scenario_id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ready")
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    vehicles_active: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trips_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    scenario = relationship("SimulationScenario", back_populates="runs")
