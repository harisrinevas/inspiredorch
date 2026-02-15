"""Initial schema: jobs, dags, dag_edges, runs, job_run_states, global_settings.

Revision ID: 001
Revises:
Create Date: 2025-02-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("handler_config", sa.Text(), nullable=False),
        sa.Column("input_spec", sa.Text(), nullable=True),
        sa.Column("output_spec", sa.Text(), nullable=True),
        sa.Column("input_validation_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("output_validation_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("validator_config", sa.Text(), nullable=True),
        sa.Column("concurrency_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_name", "jobs", ["name"])

    op.create_table(
        "dags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("schedule_cron", sa.String(128), nullable=True),
        sa.Column("schedule_timezone", sa.String(64), nullable=True),
        sa.Column("paused", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("retention_days_override", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_dags_name", "dags", ["name"])

    op.create_table(
        "dag_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dag_id", sa.String(36), sa.ForeignKey("dags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_job_id", sa.String(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_job_id", sa.String(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_dag_edges_dag_id", "dag_edges", ["dag_id"])
    op.create_index("ix_dag_edges_from_job_id", "dag_edges", ["from_job_id"])
    op.create_index("ix_dag_edges_to_job_id", "dag_edges", ["to_job_id"])

    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dag_id", sa.String(36), sa.ForeignKey("dags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trigger_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_runs_dag_id", "runs", ["dag_id"])
    op.create_index("ix_runs_status", "runs", ["status"])

    op.create_table(
        "job_run_states",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("logs_ref", sa.String(512), nullable=True),
    )
    op.create_index("ix_job_run_states_run_id", "job_run_states", ["run_id"])
    op.create_index("ix_job_run_states_job_id", "job_run_states", ["job_id"])
    op.create_index("ix_job_run_states_status", "job_run_states", ["status"])

    op.create_table(
        "global_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.String(512), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("job_run_states")
    op.drop_table("runs")
    op.drop_table("dag_edges")
    op.drop_table("dags")
    op.drop_table("jobs")
    op.drop_table("global_settings")
