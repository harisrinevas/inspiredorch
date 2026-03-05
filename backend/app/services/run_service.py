"""Run creation and state management service."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.run import (
    Run,
    JobRunState,
    RUN_STATUS_PENDING,
    RUN_STATUS_RUNNING,
    RUN_STATUS_SUCCESS,
    RUN_STATUS_FAILED,
    RUN_STATUS_CANCELLED,
    JOB_RUN_STATUS_PENDING,
    JOB_RUN_STATUS_SUCCESS,
    JOB_RUN_STATUS_FAILED,
    JOB_RUN_STATUS_SKIPPED,
    JOB_RUN_STATUS_CANCELLED,
    JOB_RUN_STATUS_RUNNING,
    JOB_RUN_STATUS_INPUT_VALIDATION,
    JOB_RUN_STATUS_OUTPUT_VALIDATION,
)
from app.repositories.run_repository import RunRepository
from app.repositories.job_run_state_repository import JobRunStateRepository
from app.schemas.run import JobRunStateResponse, RunResponse, RunListItem


def run_to_dict(run: Run) -> dict:
    states = [job_state_to_dict(s) for s in (run.job_run_states or [])]
    return {
        "id": run.id,
        "dag_id": run.dag_id,
        "trigger_time": run.trigger_time,
        "triggered_by": run.triggered_by,
        "status": run.status,
        "created_at": run.created_at,
        "job_run_states": states,
    }


def run_list_item_to_dict(run: Run) -> dict:
    return {
        "id": run.id,
        "dag_id": run.dag_id,
        "trigger_time": run.trigger_time,
        "triggered_by": run.triggered_by,
        "status": run.status,
        "created_at": run.created_at,
    }


def job_state_to_dict(s: JobRunState) -> dict:
    return {
        "id": s.id,
        "run_id": s.run_id,
        "job_id": s.job_id,
        "status": s.status,
        "started_at": s.started_at,
        "finished_at": s.finished_at,
        "error_message": s.error_message,
        "logs_ref": s.logs_ref,
    }


class RunService:
    def __init__(self, db: Session):
        self.run_repo = RunRepository(db)
        self.state_repo = JobRunStateRepository(db)
        self.db = db

    def create_run(self, dag_id: str, job_ids: list[str], triggered_by: Optional[str] = None) -> Run:
        run = self.run_repo.create_run(dag_id, triggered_by=triggered_by)
        for job_id in job_ids:
            self.state_repo.create(run.id, job_id)
        self.db.commit()
        return self.run_repo.get_with_job_states(run.id)

    def get(self, run_id: str) -> Optional[Run]:
        return self.run_repo.get_with_job_states(run_id)

    def list_by_dag(self, dag_id: str, limit: int = 100) -> list[Run]:
        return self.run_repo.list_by_dag(dag_id, limit=limit)

    def list_all(self, limit: int = 200) -> list[Run]:
        return self.db.query(Run).order_by(Run.trigger_time.desc()).limit(limit).all()

    def update_run_status(self, run_id: str, status: str) -> None:
        run = self.run_repo.get(run_id)
        if run:
            run.status = status
            self.db.commit()

    def update_job_state(
        self,
        run_id: str,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        started_at=None,
        finished_at=None,
    ) -> None:
        state = self.state_repo.get_by_run_and_job(run_id, job_id)
        if state:
            state.status = status
            if error_message is not None:
                state.error_message = error_message
            if started_at is not None:
                state.started_at = started_at
            if finished_at is not None:
                state.finished_at = finished_at
            self.db.commit()

    def cancel_run(self, run: Run) -> bool:
        """Cancel a run if it is still pending or running. Returns True if cancelled."""
        if run.status not in (RUN_STATUS_PENDING, RUN_STATUS_RUNNING):
            return False
        run.status = RUN_STATUS_CANCELLED
        for state in run.job_run_states:
            if state.status in (JOB_RUN_STATUS_PENDING, JOB_RUN_STATUS_RUNNING):
                state.status = JOB_RUN_STATUS_CANCELLED
        self.db.commit()
        return True
