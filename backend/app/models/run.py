"""Run and JobRunState models - DAG execution state."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.base import TimestampMixin, generate_uuid


# Run status
RUN_STATUS_PENDING = "pending"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_SUCCESS = "success"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_CANCELLED = "cancelled"

# Job run status (per job in a run)
JOB_RUN_STATUS_PENDING = "pending"
JOB_RUN_STATUS_INPUT_VALIDATION = "input_validation"
JOB_RUN_STATUS_RUNNING = "running"
JOB_RUN_STATUS_OUTPUT_VALIDATION = "output_validation"
JOB_RUN_STATUS_SUCCESS = "success"
JOB_RUN_STATUS_FAILED = "failed"
JOB_RUN_STATUS_SKIPPED = "skipped"
JOB_RUN_STATUS_CANCELLED = "cancelled"


class Run(Base, TimestampMixin):
    """One execution of a DAG."""

    __tablename__ = "runs"

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
    trigger_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    triggered_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # user or "scheduler"
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=RUN_STATUS_PENDING,
        index=True,
    )

    job_run_states: Mapped[list["JobRunState"]] = relationship(
        "JobRunState",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class JobRunState(Base):
    """Per-job state for one DAG run."""

    __tablename__ = "job_run_states"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JOB_RUN_STATUS_PENDING,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)  # captured stdout/stderr
    logs_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)  # path or object key

    run: Mapped["Run"] = relationship("Run", back_populates="job_run_states")
