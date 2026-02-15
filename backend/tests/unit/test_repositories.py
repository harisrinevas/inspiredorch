"""Unit tests for repositories (Metadata & State Store)."""

import pytest
from sqlalchemy.orm import Session

from app.models import Job, DAG, DAGEdge, Run, JobRunState, GlobalSetting
from app.repositories import (
    JobRepository,
    DAGRepository,
    RunRepository,
    JobRunStateRepository,
    GlobalSettingRepository,
)


def test_job_repository_create_and_get(db_session: Session):
    repo = JobRepository(db_session)
    job = Job(
        name="test-job",
        description="A test",
        handler_config='{"type": "script", "path": "/bin/true"}',
        input_validation_enabled=True,
        concurrency_enabled=False,
    )
    repo.add(job)
    db_session.commit()
    got = repo.get(job.id)
    assert got is not None
    assert got.name == "test-job"
    assert got.input_validation_enabled is True


def test_job_repository_list_all(db_session: Session):
    repo = JobRepository(db_session)
    for name in ["job-a", "job-b"]:
        repo.add(Job(name=name, handler_config="{}"))
    db_session.commit()
    all_jobs = repo.list_all()
    assert len(all_jobs) == 2
    names = [j.name for j in all_jobs]
    assert "job-a" in names and "job-b" in names


def test_dag_repository_with_edges(db_session: Session):
    job_repo = JobRepository(db_session)
    j1 = Job(name="j1", handler_config="{}")
    j2 = Job(name="j2", handler_config="{}")
    job_repo.add(j1)
    job_repo.add(j2)
    db_session.commit()

    dag_repo = DAGRepository(db_session)
    dag = DAG(name="pipeline-1", description="First pipeline")
    dag_repo.add(dag)
    dag_repo.add_edge(dag.id, j1.id, j2.id)
    db_session.commit()

    loaded = dag_repo.get_with_edges(dag.id)
    assert loaded is not None
    assert len(loaded.edges) == 1
    assert loaded.edges[0].from_job_id == j1.id and loaded.edges[0].to_job_id == j2.id

    edges = dag_repo.get_edges(dag.id)
    assert edges == [(j1.id, j2.id)]


def test_run_repository_create_and_list(db_session: Session):
    dag_repo = DAGRepository(db_session)
    dag = DAG(name="dag1")
    dag_repo.add(dag)
    db_session.commit()

    run_repo = RunRepository(db_session)
    run = run_repo.create_run(dag.id, triggered_by="scheduler")
    db_session.commit()

    assert run.id is not None
    assert run.dag_id == dag.id
    assert run.status == "pending"

    runs = run_repo.list_by_dag(dag.id)
    assert len(runs) == 1
    assert runs[0].id == run.id


def test_job_run_state_repository(db_session: Session):
    dag_repo = DAGRepository(db_session)
    dag = DAG(name="dag1")
    dag_repo.add(dag)
    run_repo = RunRepository(db_session)
    run = run_repo.create_run(dag.id)
    db_session.commit()

    state_repo = JobRunStateRepository(db_session)
    state = state_repo.create(run.id, "some-job-id")
    db_session.commit()

    assert state.run_id == run.id
    assert state.job_id == "some-job-id"
    assert state.status == "pending"

    got = state_repo.get_by_run_and_job(run.id, "some-job-id")
    assert got is not None
    assert got.id == state.id


def test_global_setting_repository(db_session: Session):
    repo = GlobalSettingRepository(db_session)
    assert repo.get_value("retention_days") is None
    assert repo.get_retention_days() is None

    repo.set_value("retention_days", "90")
    db_session.commit()
    assert repo.get_value("retention_days") == "90"
    assert repo.get_retention_days() == 90

    repo.set_value("retention_days", "30")
    db_session.commit()
    assert repo.get_retention_days() == 30
