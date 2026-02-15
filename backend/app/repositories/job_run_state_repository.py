"""JobRunState repository - per-job state within a run."""

from sqlalchemy.orm import Session

from app.models.run import JobRunState
from app.repositories.base import BaseRepository


class JobRunStateRepository(BaseRepository[JobRunState]):
    def __init__(self, db: Session):
        super().__init__(db, JobRunState)

    def get_by_run_and_job(self, run_id: str, job_id: str) -> JobRunState | None:
        return (
            self.db.query(JobRunState)
            .filter(
                JobRunState.run_id == run_id,
                JobRunState.job_id == job_id,
            )
            .first()
        )

    def list_by_run(self, run_id: str) -> list[JobRunState]:
        return (
            self.db.query(JobRunState)
            .filter(JobRunState.run_id == run_id)
            .all()
        )

    def create(self, run_id: str, job_id: str) -> JobRunState:
        state = JobRunState(run_id=run_id, job_id=job_id)
        self.db.add(state)
        self.db.flush()
        return state
