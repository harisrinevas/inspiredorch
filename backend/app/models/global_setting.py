"""Global settings (e.g. retention default)."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GlobalSetting(Base):
    """Key-value global settings. E.g. retention_days_default (overridable by config)."""

    __tablename__ = "global_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(String(512), nullable=False)  # store as string; cast in app
