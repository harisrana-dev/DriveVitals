"""add_digital_twin_lab_schema

Revision ID: f1a2b3c4d5e6
Revises: e3a1b2c4d5f6
Create Date: 2026-09-03 00:00:00.000000

Adds the persisted Digital Twin Lab domain:

* drivers.behavior_profile (simulation input)
* vehicles: display_name, fuel_efficiency_factor, acceleration_response,
  tank_capacity_liters (simulation characteristics)
* routes: speed_limit_kmh, is_active
* new: assignments, simulation_scenarios, simulation_runs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e3a1b2c4d5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----- Drivers -----------------------------------------------------
    op.add_column(
        "drivers",
        sa.Column(
            "behavior_profile",
            sa.String(20),
            nullable=False,
            server_default="standard",
        ),
    )

    # ----- Vehicles ----------------------------------------------------
    op.add_column(
        "vehicles",
        sa.Column("display_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "fuel_efficiency_factor",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "acceleration_response",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
    )
    op.add_column(
        "vehicles",
        sa.Column(
            "tank_capacity_liters",
            sa.Float(),
            nullable=False,
            server_default="60.0",
        ),
    )

    # ----- Routes ------------------------------------------------------
    op.add_column(
        "routes",
        sa.Column(
            "speed_limit_kmh",
            sa.Float(),
            nullable=False,
            server_default="60.0",
        ),
    )
    op.add_column(
        "routes",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )

    # ----- Assignments -------------------------------------------------
    op.create_table(
        "assignments",
        sa.Column(
            "assignment_id",
            sa.String(36),
            primary_key=True,
        ),
        sa.Column(
            "driver_id",
            sa.String(36),
            sa.ForeignKey("drivers.driver_id"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.String(36),
            sa.ForeignKey("vehicles.vehicle_id"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            sa.String(36),
            sa.ForeignKey("routes.route_id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "driver_id",
            "vehicle_id",
            "route_id",
            name="uq_assignments_driver_vehicle_route",
        ),
    )
    op.create_index(
        "ix_assignments_driver_id",
        "assignments",
        ["driver_id"],
    )
    op.create_index(
        "ix_assignments_vehicle_id",
        "assignments",
        ["vehicle_id"],
    )
    op.create_index(
        "ix_assignments_route_id",
        "assignments",
        ["route_id"],
    )

    # ----- Simulation scenarios ---------------------------------------
    op.create_table(
        "simulation_scenarios",
        sa.Column(
            "scenario_id",
            sa.String(36),
            primary_key=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "simulation_speed",
            sa.Float(),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ----- Simulation runs --------------------------------------------
    op.create_table(
        "simulation_runs",
        sa.Column(
            "run_id",
            sa.String(36),
            primary_key=True,
        ),
        sa.Column(
            "scenario_id",
            sa.String(36),
            sa.ForeignKey("simulation_scenarios.scenario_id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="ready",
        ),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "vehicles_active",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "trips_completed",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_simulation_runs_scenario_id",
        "simulation_runs",
        ["scenario_id"],
    )

    # ----- Scenario <-> assignment association -------------------------
    op.create_table(
        "scenario_assignments",
        sa.Column(
            "scenario_id",
            sa.String(36),
            sa.ForeignKey("simulation_scenarios.scenario_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "assignment_id",
            sa.String(36),
            sa.ForeignKey("assignments.assignment_id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("scenario_assignments")
    op.drop_index("ix_simulation_runs_scenario_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_table("simulation_scenarios")

    op.drop_index("ix_assignments_route_id", table_name="assignments")
    op.drop_index("ix_assignments_vehicle_id", table_name="assignments")
    op.drop_index("ix_assignments_driver_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_column("routes", "is_active")
    op.drop_column("routes", "speed_limit_kmh")

    op.drop_column("vehicles", "tank_capacity_liters")
    op.drop_column("vehicles", "acceleration_response")
    op.drop_column("vehicles", "fuel_efficiency_factor")
    op.drop_column("vehicles", "display_name")

    op.drop_column("drivers", "behavior_profile")
