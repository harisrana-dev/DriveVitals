from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base, TimestampMixin


class SystemSettings(TimestampMixin, Base):
    """Persistent admin configuration storage.

    Each row represents a configuration category (e.g. ``analytics``) with
    a JSON payload.  ``updated_by`` tracks the last administrator who
    modified the category.
    """

    __tablename__ = "system_settings"

    category: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    settings_data: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
