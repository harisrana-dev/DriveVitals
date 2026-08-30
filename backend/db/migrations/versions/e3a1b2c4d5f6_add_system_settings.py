"""add_system_settings

Revision ID: e3a1b2c4d5f6
Revises: 5f4c3b2a1d0e
Create Date: 2026-08-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a1b2c4d5f6'
down_revision: Union[str, Sequence[str], None] = '5f4c3b2a1d0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the system_settings table for persistent admin configuration."""
    op.create_table(
        "system_settings",
        sa.Column("category", sa.String(64), primary_key=True),
        sa.Column("settings_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_by",
            sa.String(36),
            sa.ForeignKey("users.user_id", ondelete="SET NULL"),
            nullable=True,
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
    )


def downgrade() -> None:
    """Drop the system_settings table."""
    op.drop_table("system_settings")
