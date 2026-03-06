"""Integration tests: full Metadata & State Store workflow."""

from sqlalchemy.orm import Session

from app.models import DAG, Job
from app.repositories import (
    DAGRepository,
    GlobalSettingRepository,
    JobRepository,
    JobRunStateRepository,
    RunRepository,
)


def test_full_workflow_job_dag_run(db_session: Session):
    """Create jobs -> DAG with edges -> run -> job run states."""
    job_repo = JobRepository(db_session)
    j1 = Job(name="extract", handler_config='{"type":"script"}')
    j2 = Job(name="transform", handler_config='{"type":"script"}')
    j3 = Job(name="load", handler_config='{"type":"script"}')
    for j in (j1, j2, j3):
        job_repo.add(j)
    db_session.commit()

    dag_repo = DAGRepository(db_session)
    dag = DAG(name="etl", description="ETL pipeline")
    dag_repo.add(dag)
    dag_repo.add_edge(dag.id, j1.id, j2.id)
    dag_repo.add_edge(dag.id, j2.id, j3.id)
    db_session.commit()

    run_repo = RunRepository(db_session)
    run = run_repo.create_run(dag.id, triggered_by="api")
    db_session.commit()

    state_repo = JobRunStateRepository(db_session)
    for j in (j1, j2, j3):
        state_repo.create(run.id, j.id)
    db_session.commit()

    # Load run with states
    loaded_run = run_repo.get_with_job_states(run.id)
    assert loaded_run is not None
    assert loaded_run.dag_id == dag.id
    assert len(loaded_run.job_run_states) == 3

    # Retention: get effective retention (global default when not set)
    setting_repo = GlobalSettingRepository(db_session)
    retention = setting_repo.get_retention_days()
    assert retention is None  # not set in DB; app uses config default
    setting_repo.set_value("retention_days", "45")
    db_session.commit()
    assert setting_repo.get_retention_days() == 45
