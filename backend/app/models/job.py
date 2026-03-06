"""Job model - global job library."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, generate_uuid


class Job(Base, TimestampMixin):
    """Global job definition. Referenced by DAGs via edges."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Handler: script path, container image, or API endpoint
    handler_config: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    # Optional input/output metadata (paths, schemas, key-value)
    input_spec: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output_spec: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Validation toggles and optional config (script path, schema URI)
    input_validation_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    output_validation_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validator_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Concurrency: when True, orchestrator limits parallel runs by system capacity
    concurrency_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
