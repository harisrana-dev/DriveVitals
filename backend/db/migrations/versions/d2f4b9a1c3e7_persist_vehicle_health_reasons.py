"""persist_vehicle_health_reasons

Revision ID: d2f4b9a1c3e7
Revises: 88b38c74e612
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f4b9a1c3e7'
down_revision: Union[str, Sequence[str], None] = '88b38c74e612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Persist the canonical health reasons produced by the health engine so
    the REST vehicle-health endpoint returns the same meaning that the
    live dashboard carries over the WebSocket. Nullable because a vehicle
    may not have been through the health pipeline yet.
    """
    op.add_column(
        "vehicle_health",
        sa.Column("health_reasons", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("vehicle_health", "health_reasons")
