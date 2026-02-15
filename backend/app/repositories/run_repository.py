"""Run repository - DAG execution records."""

from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.run import Run, JobRunState
from app.repositories.base import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self, db: Session):
        super().__init__(db, Run)

    def get_with_job_states(self, id: str) -> Run | None:
        return (
            self.db.query(Run)
            .options(joinedload(Run.job_run_states))
            .filter(Run.id == id)
            .first()
        )

    def list_by_dag(self, dag_id: str, limit: int = 100) -> list[Run]:
        return (
            self.db.query(Run)
            .filter(Run.dag_id == dag_id)
            .order_by(Run.trigger_time.desc())
            .limit(limit)
            .all()
        )

    def list_runs_older_than(self, cutoff: datetime) -> list[Run]:
        """For retention sweep: runs with trigger_time < cutoff."""
        return self.db.query(Run).filter(Run.trigger_time < cutoff).all()

    def create_run(self, dag_id: str, triggered_by: str | None = None) -> Run:
        run = Run(dag_id=dag_id, triggered_by=triggered_by)
        self.db.add(run)
        self.db.flush()
        return run
