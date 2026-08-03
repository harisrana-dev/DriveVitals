"""add_driver_statistics_scores

Revision ID: 5b3897eb7028
Revises: 4c251373e911
Create Date: 2026-08-03 13:08:18.602373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b3897eb7028'
down_revision: Union[str, Sequence[str], None] = '4c251373e911'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "driver_statistics",
        sa.Column(
            "aggression_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )
    op.add_column(
        "driver_statistics",
        sa.Column(
            "efficiency_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("driver_statistics", "efficiency_score")
    op.drop_column("driver_statistics", "aggression_score")
