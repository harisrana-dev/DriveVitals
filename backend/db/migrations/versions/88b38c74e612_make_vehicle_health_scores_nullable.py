"""make_vehicle_health_scores_nullable

Revision ID: 88b38c74e612
Revises: 5b3897eb7028
Create Date: 2026-08-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88b38c74e612'
down_revision: Union[str, Sequence[str], None] = '5b3897eb7028'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCORE_COLUMNS = (
    "overall_health_score",
    "engine_health",
    "brake_health",
    "transmission_health",
    "cooling_health",
    "fuel_system_health",
)


def upgrade() -> None:
    """Upgrade schema.

    Health scores may be unknown (e.g. no telemetry has been seen for a
    vehicle yet). A missing score must not be fabricated as 100.0, so the
    columns become nullable and persist None instead.
    """
    for column in _SCORE_COLUMNS:
        op.alter_column(
            "vehicle_health",
            column,
            existing_type=sa.Float(),
            nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    for column in _SCORE_COLUMNS:
        op.alter_column(
            "vehicle_health",
            column,
            existing_type=sa.Float(),
            nullable=False,
        )
