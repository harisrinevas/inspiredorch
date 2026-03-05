"""Scheduler Service: triggers DAG runs on cron schedules.

Every `interval_seconds`, the scheduler:
  1. Queries all non-paused DAGs with a schedule_cron.
  2. For each, uses croniter to find the previous fire time.
  3. If no run exists since that fire time, creates and triggers a run.
"""

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from croniter import croniter

from app.db.session import SessionLocal
from app.repositories.dag_repository import DAGRepository
from app.repositories.run_repository import RunRepository
from app.services.dag_service import DAGService
from app.services.run_service import RunService

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="scheduler")
        self._thread.start()
        logger.info("Scheduler started (interval=%ds)", self.interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                logger.exception("Scheduler tick error")
            self._stop_event.wait(timeout=self.interval)

    def _tick(self) -> None:
        from app.services.execution_engine import ExecutionEngine

        db = SessionLocal()
        try:
            dag_repo = DAGRepository(db)
            run_repo = RunRepository(db)
            engine = ExecutionEngine()

            now = datetime.now(tz=timezone.utc)
            dags = db.query(__import__("app.models.dag", fromlist=["DAG"]).DAG).filter_by(paused=False).all()

            for dag in dags:
                if not dag.schedule_cron:
                    continue
                try:
                    self._maybe_trigger(dag, now, dag_repo, run_repo, engine)
                except Exception:
                    logger.exception("Scheduler error for DAG %s", dag.id)
        finally:
            db.close()

    def _maybe_trigger(self, dag, now, dag_repo, run_repo, engine) -> None:
        from app.services.execution_engine import ExecutionEngine
        from app.db.session import SessionLocal

        try:
            cron = croniter(dag.schedule_cron, now)
            prev_fire = cron.get_prev(datetime)
        except Exception:
            logger.warning("Invalid cron '%s' for DAG %s", dag.schedule_cron, dag.id)
            return

        # Make prev_fire timezone-aware
        if prev_fire.tzinfo is None:
            prev_fire = prev_fire.replace(tzinfo=timezone.utc)

        # Check if we already have a run triggered at or after prev_fire
        recent_runs = run_repo.list_by_dag(dag.id, limit=1)
        if recent_runs:
            last_trigger = recent_runs[0].trigger_time
            if last_trigger.tzinfo is None:
                last_trigger = last_trigger.replace(tzinfo=timezone.utc)
            if last_trigger >= prev_fire:
                return  # Already triggered for this schedule slot

        logger.info("Scheduler: triggering DAG %s (cron=%s)", dag.id, dag.schedule_cron)

        # Create run in a new session to avoid state conflicts
        db2 = SessionLocal()
        try:
            dag_svc = DAGService(db2)
            run_svc = RunService(db2)
            full_dag = dag_svc.get(dag.id)
            if not full_dag:
                return
            job_ids = dag_svc.get_job_ids(full_dag)
            run = run_svc.create_run(dag.id, job_ids, triggered_by="scheduler")
            run_id = run.id
        finally:
            db2.close()

        ExecutionEngine().trigger(run_id)
