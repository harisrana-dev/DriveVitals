"""initial_schema

Revision ID: 020b8a858c0a
Revises:
Create Date: 2026-07-30 12:12:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020b8a858c0a"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", sa.String(36), primary_key=True),
        sa.Column("registration_number", sa.String(50), nullable=False),
        sa.Column("vin", sa.String(17), nullable=False),
        sa.Column("manufacturer", sa.String(50), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("fuel_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_vehicles_registration_number", "vehicles", ["registration_number"], unique=True)
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"], unique=True)

    op.create_table(
        "drivers",
        sa.Column("driver_id", sa.String(36), primary_key=True),
        sa.Column("first_name", sa.String(50), nullable=False),
        sa.Column("last_name", sa.String(50), nullable=False),
        sa.Column("license_number", sa.String(30), nullable=False),
        sa.Column(
            "employment_status", sa.String(20), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_drivers_license_number", "drivers", ["license_number"], unique=True)

    op.create_table(
        "routes",
        sa.Column("route_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("route_type", sa.String(30), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("destination", sa.Text(), nullable=False),
        sa.Column("estimated_distance_km", sa.Float(), nullable=False),
    )

    op.create_table(
        "trips",
        sa.Column("trip_id", sa.String(36), primary_key=True),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("route_id", sa.String(36), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("fuel_used_liters", sa.Float(), nullable=True),
        sa.Column("average_speed_kmh", sa.Float(), nullable=True),
        sa.Column("maximum_speed_kmh", sa.Float(), nullable=True),
        sa.Column("trip_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="assigned"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.driver_id"]),
        sa.ForeignKeyConstraint(["route_id"], ["routes.route_id"]),
    )
    op.create_index("ix_trips_vehicle_id", "trips", ["vehicle_id"])
    op.create_index("ix_trips_driver_id", "trips", ["driver_id"])

    op.create_table(
        "telemetry_samples",
        sa.Column("sample_id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=False),
        sa.Column("rpm", sa.Float(), nullable=False),
        sa.Column("engine_load_percent", sa.Float(), nullable=False),
        sa.Column("throttle_percent", sa.Float(), nullable=False),
        sa.Column("brake_percent", sa.Float(), nullable=False),
        sa.Column("fuel_rate_lph", sa.Float(), nullable=False),
        sa.Column("fuel_level_percent", sa.Float(), nullable=False),
        sa.Column("coolant_temperature_c", sa.Float(), nullable=False),
        sa.Column("odometer_km", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.trip_id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
    )
    op.create_index("ix_telemetry_samples_trip_id", "telemetry_samples", ["trip_id"])
    op.create_index("ix_telemetry_samples_vehicle_id", "telemetry_samples", ["vehicle_id"])
    op.create_index("ix_telemetry_samples_timestamp", "telemetry_samples", ["timestamp"])

    op.create_table(
        "behaviour_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("trip_id", sa.String(36), nullable=False),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("maximum_value", sa.Float(), nullable=False),
        sa.Column("average_value", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.trip_id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.driver_id"]),
    )
    op.create_index("ix_behaviour_events_trip_id", "behaviour_events", ["trip_id"])
    op.create_index("ix_behaviour_events_vehicle_id", "behaviour_events", ["vehicle_id"])

    op.create_table(
        "alerts",
        sa.Column("alert_id", sa.String(36), primary_key=True),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("driver_id", sa.String(36), nullable=True),
        sa.Column("trip_id", sa.String(36), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.driver_id"]),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.trip_id"]),
    )
    op.create_index("ix_alerts_vehicle_id", "alerts", ["vehicle_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])

    op.create_table(
        "maintenance_records",
        sa.Column("maintenance_id", sa.String(36), primary_key=True),
        sa.Column("vehicle_id", sa.String(36), nullable=False),
        sa.Column("maintenance_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("due_odometer_km", sa.Float(), nullable=True),
        sa.Column("completed_odometer_km", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
    )
    op.create_index(
        "ix_maintenance_records_vehicle_id", "maintenance_records", ["vehicle_id"]
    )
    op.create_index("ix_maintenance_records_status", "maintenance_records", ["status"])

    op.create_table(
        "vehicle_health",
        sa.Column("vehicle_id", sa.String(36), primary_key=True),
        sa.Column("overall_health_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("engine_health", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("brake_health", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column(
            "transmission_health", sa.Float(), nullable=False, server_default="100.0"
        ),
        sa.Column("cooling_health", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column(
            "fuel_system_health", sa.Float(), nullable=False, server_default="100.0"
        ),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
    )

    op.create_table(
        "driver_statistics",
        sa.Column("driver_id", sa.String(36), primary_key=True),
        sa.Column("total_trips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_distance_km", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "total_driving_time_seconds",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "average_trip_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("fuel_efficiency", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("speeding_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "harsh_braking_events", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "aggressive_throttle_events",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("high_rpm_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("safety_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.driver_id"]),
    )

    op.create_table(
        "vehicle_statistics",
        sa.Column("vehicle_id", sa.String(36), primary_key=True),
        sa.Column("trip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "total_distance_km", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "total_runtime_seconds", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "fuel_consumed_liters", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "average_fuel_efficiency",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "lifetime_health_score",
            sa.Float(),
            nullable=False,
            server_default="100.0",
        ),
        sa.Column(
            "utilization_percent", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"]),
    )


def downgrade() -> None:
    op.drop_table("vehicle_statistics")
    op.drop_table("driver_statistics")
    op.drop_table("vehicle_health")
    op.drop_table("maintenance_records")
    op.drop_table("alerts")
    op.drop_table("behaviour_events")
    op.drop_table("telemetry_samples")
    op.drop_table("trips")
    op.drop_table("routes")
    op.drop_table("drivers")
    op.drop_table("vehicles")
