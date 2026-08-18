"""add last_triggered_at to alerts

Revision ID: b3c8d9e2f1a4
Revises: a7a996678ad6
Create Date: 2026-08-17
"""
from alembic import op
import sqlalchemy as sa

revision = "b3c8d9e2f1a4"
down_revision = "a7a996678ad6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column(
            "last_triggered_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("alerts", "last_triggered_at")
