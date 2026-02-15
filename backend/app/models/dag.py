"""DAG and DAGEdge models."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.base import TimestampMixin, generate_uuid


class DAG(Base, TimestampMixin):
    """Pipeline: graph of jobs (from global library) and dependencies."""

    __tablename__ = "dags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Schedule (optional)
    schedule_cron: Mapped[str | None] = mapped_column(String(128), nullable=True)
    schedule_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Retention: null = use global default; otherwise override in days
    retention_days_override: Mapped[int | None] = mapped_column(nullable=True)

    edges: Mapped[list["DAGEdge"]] = relationship(
        "DAGEdge",
        back_populates="dag",
        cascade="all, delete-orphan",
        foreign_keys="DAGEdge.dag_id",
    )


class DAGEdge(Base):
    """Directed edge (from_job_id -> to_job_id) in a DAG. No cycles allowed."""

    __tablename__ = "dag_edges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    dag_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dag: Mapped["DAG"] = relationship("DAG", back_populates="edges")
