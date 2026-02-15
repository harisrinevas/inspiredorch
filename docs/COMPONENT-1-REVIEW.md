# Component 1: Metadata & State Store — Review

## Scope

First component of the implementation plan: **Metadata & State Store** — schema and repository layer only (no API, no UI).

## Delivered

### 1. Project structure

- `backend/` — FastAPI app, DB, models, repositories, tests
- `frontend/` — (placeholder for React; not created yet)
- `docs/` — design and review docs
- `scripts/` — (install script for Linux/WSL in a later pass)

### 2. Database schema (PostgreSQL/SQLite)

- **jobs** — Global job library: id, name, description, handler_config, input_spec, output_spec, input_validation_enabled, output_validation_enabled, validator_config, concurrency_enabled, created_at, updated_at
- **dags** — id, name, description, schedule_cron, schedule_timezone, paused, retention_days_override, created_at, updated_at
- **dag_edges** — id, dag_id, from_job_id, to_job_id (FK to jobs)
- **runs** — id, dag_id, trigger_time, triggered_by, status, created_at, updated_at
- **job_run_states** — id, run_id, job_id, status, started_at, finished_at, error_message, logs_ref
- **global_settings** — key, value (e.g. retention_days for global default)

### 3. Repository layer

- `JobRepository` — get, add, list_all, list_by_ids, exists
- `DAGRepository` — get, add, list_all, get_with_edges, get_edges, add_edge, delete_edges
- `RunRepository` — get, create_run, get_with_job_states, list_by_dag, list_runs_older_than (for retention)
- `JobRunStateRepository` — get, create, get_by_run_and_job, list_by_run
- `GlobalSettingRepository` — get_value, set_value, get_retention_days

### 4. Migrations

- Alembic configured; initial migration `001_initial_metadata_store.py` creates all tables.

### 5. Application shell

- FastAPI app with `/health` and `/ready` only (no DAG/Job API yet).
- Config via pydantic-settings (env + .env); default DB URL SQLite for local dev.

### 6. Tests

- **Unit:** `tests/unit/test_repositories.py` — CRUD and list operations for all repositories.
- **Integration:** `tests/integration/test_metadata_store.py` — full workflow: jobs → DAG with edges → run → job run states; global retention setting.

## How to run

```bash
cd backend
python -m venv .venv
# Linux/WSL: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional: cp .env.example .env
alembic upgrade head
pytest
uvicorn app.main:app --reload
# GET http://localhost:8000/health
```

## Design alignment

- **Retention:** Global default from config (`retention_days_default=90`); overridable per DAG via `dags.retention_days_override`; runtime value from `GlobalSettingRepository.get_retention_days()` or config. Retention sweep (delete/archive old runs) will use “current setting at execution time” — to be implemented with Scheduler/Engine.
- **Consistency:** Repositories use a single session; run creation and state updates intended to be used inside transactions by callers (e.g. Execution Engine).

## Pending (later components)

- DAG/Job Management Service (cycle validation, CRUD API)
- API Gateway with auth
- Execution Engine and Workers
- Scheduler and retention sweep job
- Web UI
- Linux/WSL install script and docs

## Requested review

Please confirm:

1. Project structure and naming are acceptable.
2. Schema (tables and columns) match DESIGN.md and locked decisions.
3. Repository APIs are sufficient for the next component (DAG/Job Management Service).
4. Any changes before proceeding to Component 2 (DAG/Job Management Service).
