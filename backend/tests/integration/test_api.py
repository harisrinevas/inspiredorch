"""Integration tests: REST API via TestClient."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so they register with Base.metadata before create_all
import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    # StaticPool ensures all sessions share the same in-memory SQLite connection
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


# ── Health ─────────────────────────────────────────────────────────────────────


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200


# ── Jobs ───────────────────────────────────────────────────────────────────────


def test_create_job(client):
    r = client.post(
        "/jobs",
        json={
            "name": "my-job",
            "handler_config": {"type": "noop"},
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "my-job"
    assert data["handler_config"] == {"type": "noop"}
    assert "id" in data


def test_list_jobs(client):
    r = client.get("/jobs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_job(client):
    # Create first
    r = client.post("/jobs", json={"name": "fetch-job", "handler_config": {"type": "noop"}})
    job_id = r.json()["id"]

    r = client.get(f"/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json()["id"] == job_id


def test_get_job_not_found(client):
    r = client.get("/jobs/does-not-exist")
    assert r.status_code == 404


def test_update_job(client):
    r = client.post("/jobs", json={"name": "old-name", "handler_config": {"type": "noop"}})
    job_id = r.json()["id"]

    r = client.put(f"/jobs/{job_id}", json={"name": "new-name"})
    assert r.status_code == 200
    assert r.json()["name"] == "new-name"


def test_delete_job(client):
    r = client.post("/jobs", json={"name": "to-delete", "handler_config": {"type": "noop"}})
    job_id = r.json()["id"]

    r = client.delete(f"/jobs/{job_id}")
    assert r.status_code == 204

    r = client.get(f"/jobs/{job_id}")
    assert r.status_code == 404


# ── DAGs ───────────────────────────────────────────────────────────────────────


def _create_job(client, name="j"):
    r = client.post("/jobs", json={"name": name, "handler_config": {"type": "noop"}})
    return r.json()["id"]


def test_create_dag(client):
    j1 = _create_job(client, "dag-j1")
    j2 = _create_job(client, "dag-j2")

    r = client.post(
        "/dags",
        json={
            "name": "my-pipeline",
            "job_ids": [j1, j2],
            "edges": [{"from_job_id": j1, "to_job_id": j2}],
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "my-pipeline"
    assert len(data["edges"]) == 1


def test_create_dag_cycle_rejected(client):
    j1 = _create_job(client, "cycle-j1")
    j2 = _create_job(client, "cycle-j2")

    r = client.post(
        "/dags",
        json={
            "name": "bad",
            "job_ids": [j1, j2],
            "edges": [
                {"from_job_id": j1, "to_job_id": j2},
                {"from_job_id": j2, "to_job_id": j1},
            ],
        },
    )
    assert r.status_code == 422


def test_validate_dag(client):
    j1 = _create_job(client, "val-j1")
    j2 = _create_job(client, "val-j2")
    r = client.post(
        "/dags",
        json={
            "name": "valid-dag",
            "job_ids": [j1, j2],
            "edges": [{"from_job_id": j1, "to_job_id": j2}],
        },
    )
    dag_id = r.json()["id"]

    r = client.post(f"/dags/{dag_id}/validate")
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert len(body["execution_waves"]) == 2


def test_trigger_and_get_run(client):
    j1 = _create_job(client, "run-j1")
    r = client.post("/dags", json={"name": "run-dag", "job_ids": [j1], "edges": []})
    dag_id = r.json()["id"]

    r = client.post(f"/dags/{dag_id}/runs", json={"triggered_by": "test"})
    assert r.status_code == 201
    run = r.json()
    assert run["dag_id"] == dag_id
    assert run["status"] in ("pending", "running", "success")

    r = client.get(f"/runs/{run['id']}")
    assert r.status_code == 200


def test_list_all_runs(client):
    r = client.get("/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cancel_terminal_run_rejected(client):
    j1 = _create_job(client, "cancel-j1")
    r = client.post("/dags", json={"name": "cancel-dag", "job_ids": [j1], "edges": []})
    dag_id = r.json()["id"]

    r = client.post(f"/dags/{dag_id}/runs", json={})
    run_id = r.json()["id"]

    # Wait briefly for the noop job to complete
    import time

    time.sleep(0.5)

    r = client.get(f"/runs/{run_id}")
    status = r.json()["status"]
    if status == "success":
        r = client.post(f"/runs/{run_id}/cancel")
        assert r.status_code == 409  # already terminal


# ── Settings ───────────────────────────────────────────────────────────────────


def test_get_retention(client):
    r = client.get("/settings/retention")
    assert r.status_code == 200
    assert r.json()["key"] == "retention_days"


def test_update_retention(client):
    r = client.put("/settings/retention", json={"retention_days": 30})
    assert r.status_code == 200
    assert r.json()["value"] == "30"

    r = client.get("/settings/retention")
    assert r.json()["value"] == "30"
