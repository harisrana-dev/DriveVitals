"""drop vehicle_health score server defaults

Revision ID: b7d1f3a9c2e5
Revises: a4b5c6d7e8f9
Create Date: 2026-09-26 00:00:00.000000

Corrective migration for the forensic finding on ``88b38c74e612``.

``88b38c74e612`` made the ``vehicle_health`` score columns nullable
(unknown health must persist as ``None``, never as a fabricated 100.0)
but only rendered ``ALTER COLUMN ... DROP NOT NULL``. The original
``server_default='100.0'`` from the initial schema survived, so on any
database created by the migration chain an INSERT that omits a score
column still silently receives 100.0 — a fabricated perfect health score
that contradicts the model (``nullable=True``, no server default).

This migration drops those defaults. It is additive: already-applied
history (88b38c74e612) is left untouched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d1f3a9c2e5'
down_revision: Union[str, Sequence[str], None] = 'a4b5c6d7e8f9'
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
    """Upgrade schema: remove the fabricated 100.0 health default.

    After this migration a missing score is persisted as NULL (the model
    and the API already treat ``None`` as "unknown"), so no write path can
    invent a perfect health score by omitting a column.
    """
    for column in _SCORE_COLUMNS:
        op.alter_column(
            "vehicle_health",
            column,
            existing_type=sa.Float(),
            nullable=True,
            server_default=None,
        )


def downgrade() -> None:
    """Downgrade schema: restore the original 100.0 server default.

    Only restores the pre-M5.2 schema shape; it does not fabricate data.
    """
    for column in _SCORE_COLUMNS:
        op.alter_column(
            "vehicle_health",
            column,
            existing_type=sa.Float(),
            nullable=True,
            server_default=sa.text("'100.0'"),
        )
