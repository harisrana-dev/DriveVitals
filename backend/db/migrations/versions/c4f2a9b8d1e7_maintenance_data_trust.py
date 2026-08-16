"""maintenance_data_trust

Revision ID: c4f2a9b8d1e7
Revises: a7a996678ad6
Create Date: 2026-08-16 12:00:00.000000

Adds the maintenance data-trust columns (due_date, component, reason,
recommended_action, estimated_cost), backfills due_date from created_at
(which previously held the projected service date), and consolidates the
legacy duplicate pending projections left behind by earlier generators
into a single pending work item per (vehicle_id, maintenance_type).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4f2a9b8d1e7'
down_revision: Union[str, Sequence[str], None] = 'a7a996678ad6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'maintenance_records',
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'maintenance_records',
        sa.Column('component', sa.String(length=100), nullable=True),
    )
    op.add_column(
        'maintenance_records',
        sa.Column('reason', sa.Text(), nullable=True),
    )
    op.add_column(
        'maintenance_records',
        sa.Column('recommended_action', sa.Text(), nullable=True),
    )
    op.add_column(
        'maintenance_records',
        sa.Column('estimated_cost', sa.Float(), nullable=True),
    )
    op.create_index(
        op.f('ix_maintenance_records_vehicle_type'),
        'maintenance_records',
        ['vehicle_id', 'maintenance_type'],
        unique=False,
    )

    # created_at historically held the projected service date (the true
    # creation time was never recorded). Recover it as the explicit due date
    # before new records start writing a real created_at.
    op.execute(
        sa.text(
            "UPDATE maintenance_records "
            "SET due_date = created_at "
            "WHERE due_date IS NULL"
        )
    )

    # Consolidate legacy duplicate pending projections. Keep the canonical
    # ``{vehicle_id}:{maintenance_type}`` row when present, otherwise the
    # most recently created row. Remove the rest.
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT maintenance_id,
                       row_number() OVER (
                           PARTITION BY vehicle_id, maintenance_type
                           ORDER BY
                               CASE
                                   WHEN maintenance_id =
                                        vehicle_id || ':' || maintenance_type
                                       THEN 0
                                   ELSE 1
                               END,
                               created_at DESC,
                               maintenance_id
                       ) AS rn
                FROM maintenance_records
                WHERE status = 'pending'
            )
            DELETE FROM maintenance_records
            WHERE maintenance_id IN (
                SELECT maintenance_id FROM ranked WHERE rn > 1
            )
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('ix_maintenance_records_vehicle_type'),
        table_name='maintenance_records',
    )
    op.drop_column('maintenance_records', 'estimated_cost')
    op.drop_column('maintenance_records', 'recommended_action')
    op.drop_column('maintenance_records', 'reason')
    op.drop_column('maintenance_records', 'component')
    op.drop_column('maintenance_records', 'due_date')
