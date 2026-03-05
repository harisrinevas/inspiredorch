"""Unit tests for DAG service: cycle detection, topological sort, CRUD."""

import pytest
from sqlalchemy.orm import Session

from app.models import DAG, Job
from app.repositories import DAGRepository, JobRepository
from app.schemas.dag import DAGCreate, DAGUpdate, EdgeInput
from app.services.dag_service import (
    DAGError,
    DAGService,
    _has_cycle,
    topological_waves,
)


# ── Cycle detection ──────────────────────────────────────────────────────────

def test_no_cycle_linear():
    assert not _has_cycle({"a", "b", "c"}, [("a", "b"), ("b", "c")])


def test_no_cycle_diamond():
    assert not _has_cycle({"a", "b", "c", "d"}, [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])


def test_cycle_simple():
    assert _has_cycle({"a", "b"}, [("a", "b"), ("b", "a")])


def test_cycle_self_loop():
    assert _has_cycle({"a"}, [("a", "a")])


def test_cycle_three_nodes():
    assert _has_cycle({"a", "b", "c"}, [("a", "b"), ("b", "c"), ("c", "a")])


# ── Topological waves ─────────────────────────────────────────────────────────

def test_topo_linear():
    waves = topological_waves(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert waves == [["a"], ["b"], ["c"]]


def test_topo_diamond():
    waves = topological_waves(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
    assert waves[0] == ["a"]
    assert set(waves[1]) == {"b", "c"}
    assert waves[2] == ["d"]


def test_topo_no_edges():
    waves = topological_waves(["a", "b"], [])
    assert len(waves) == 1
    assert set(waves[0]) == {"a", "b"}


# ── DAGService CRUD ───────────────────────────────────────────────────────────

def _make_job(db: Session, name: str) -> Job:
    repo = JobRepository(db)
    j = Job(name=name, handler_config='{"type":"noop"}')
    repo.add(j)
    db.commit()
    return j


def test_dag_service_create(db_session: Session):
    j1 = _make_job(db_session, "job-1")
    j2 = _make_job(db_session, "job-2")

    svc = DAGService(db_session)
    dag = svc.create(DAGCreate(
        name="pipeline",
        job_ids=[j1.id, j2.id],
        edges=[EdgeInput(from_job_id=j1.id, to_job_id=j2.id)],
    ))

    assert dag.id is not None
    assert dag.name == "pipeline"
    assert len(dag.edges) == 1


def test_dag_service_rejects_cycle(db_session: Session):
    j1 = _make_job(db_session, "a")
    j2 = _make_job(db_session, "b")

    svc = DAGService(db_session)
    with pytest.raises(DAGError, match="cycle"):
        svc.create(DAGCreate(
            name="cyclic",
            job_ids=[j1.id, j2.id],
            edges=[
                EdgeInput(from_job_id=j1.id, to_job_id=j2.id),
                EdgeInput(from_job_id=j2.id, to_job_id=j1.id),
            ],
        ))


def test_dag_service_rejects_unknown_job(db_session: Session):
    svc = DAGService(db_session)
    with pytest.raises(DAGError, match="not found"):
        svc.create(DAGCreate(
            name="bad",
            job_ids=["nonexistent-id"],
            edges=[],
        ))


def test_dag_service_update_pause(db_session: Session):
    j1 = _make_job(db_session, "j1")
    svc = DAGService(db_session)
    dag = svc.create(DAGCreate(name="dag", job_ids=[j1.id], edges=[]))
    assert not dag.paused

    dag = svc.update(dag, DAGUpdate(paused=True))
    assert dag.paused


def test_dag_service_delete(db_session: Session):
    j1 = _make_job(db_session, "j1")
    svc = DAGService(db_session)
    dag = svc.create(DAGCreate(name="to-delete", job_ids=[j1.id], edges=[]))
    dag_id = dag.id

    svc.delete(dag)
    assert svc.get(dag_id) is None


def test_dag_execution_waves(db_session: Session):
    j1 = _make_job(db_session, "extract")
    j2 = _make_job(db_session, "transform")
    j3 = _make_job(db_session, "load")

    svc = DAGService(db_session)
    dag = svc.create(DAGCreate(
        name="etl",
        job_ids=[j1.id, j2.id, j3.id],
        edges=[
            EdgeInput(from_job_id=j1.id, to_job_id=j2.id),
            EdgeInput(from_job_id=j2.id, to_job_id=j3.id),
        ],
    ))

    waves = svc.get_execution_waves(dag)
    assert len(waves) == 3
    assert waves[0] == [j1.id]
    assert waves[1] == [j2.id]
    assert waves[2] == [j3.id]
