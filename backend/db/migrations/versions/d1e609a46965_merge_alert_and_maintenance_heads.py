"""merge alert_and_maintenance_heads

Revision ID: d1e609a46965
Revises: b3c8d9e2f1a4, c4f2a9b8d1e7
Create Date: 2026-08-18 11:45:55.652303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e609a46965'
down_revision: Union[str, Sequence[str], None] = ('b3c8d9e2f1a4', 'c4f2a9b8d1e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
