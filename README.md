# Data Pipeline Orchestrator

A simpler, DAG-based pipeline orchestrator with optional input/output validation, global job library, cron scheduling, and a React web UI. See [DESIGN.md](DESIGN.md) for architecture and decisions.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (default) / PostgreSQL, Alembic, croniter
- **Frontend:** React 18 + Vite, react-router-dom
- **Install target:** Linux / WSL / Windows

## Project structure

```
inspiredorch/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/               # REST routes (dags, jobs, runs, settings)
│   │   ├── config.py          # Settings (env / .env file)
│   │   ├── core/              # Security helpers
│   │   ├── db/                # SQLAlchemy base, session
│   │   ├── models/            # ORM models (DAG, Job, Run, JobRunState, GlobalSetting)
│   │   ├── repositories/      # Data access layer
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic (DAGService, ExecutionEngine, SchedulerService, RunService)
│   ├── tests/
│   │   ├── unit/              # Cycle detection, CRUD, repository tests
│   │   └── integration/       # API and metadata store integration tests
│   ├── alembic/               # DB migrations
│   └── requirements.txt
├── frontend/                  # React UI
│   ├── src/
│   │   ├── pages/             # DAGs, Jobs, Runs, RunDetail, Settings, Dashboard
│   │   ├── components/        # Nav, StatusBadge
│   │   └── api.js             # API client
│   └── package.json
├── docs/                      # Additional documentation
├── scripts/                   # Install and utility scripts
├── DESIGN.md
└── README.md
```

## Implementation status

| Component | Status |
|-----------|--------|
| 1. Metadata & State Store | Done |
| 2. DAG / Job Management Service | Done |
| 3. API Gateway / BFF | Done |
| 4. Execution Engine + Workers | Done |
| 5. Scheduler Service | Done |
| 6. Web UI | Done |

## Quick start

### Backend

Requires Python 3.11+. SQLite is used by default (no separate DB install needed for local dev).

```bash
cd backend
python -m venv .venv
# Linux/WSL: source .venv/bin/activate
# Windows:   .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # edit if needed (see Configuration below)
alembic upgrade head
uvicorn app.main:app --reload
```

API base: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Frontend

Requires Node.js 18+.

```bash
cd frontend
npm install
npm run dev
```

UI: `http://localhost:5173`

## Configuration

All settings are read from environment variables or a `.env` file in the `backend/` directory.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./orchestrator.db` | DB connection string. For PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/db` |
| `API_KEY` | _(unset)_ | If set, all API endpoints require `X-Api-Key: <value>` header. Leave unset for open dev mode. |
| `RETENTION_DAYS_DEFAULT` | `90` | Global run retention in days (overridable per DAG via API). |
| `SCHEDULER_INTERVAL_SECONDS` | `60` | How often the scheduler polls for due DAG schedules. |
| `DEBUG` | `false` | Enable debug mode. |

## API overview

All endpoints are authenticated via `X-Api-Key` header when `API_KEY` is configured. Full interactive spec at `/docs`.

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/jobs` | List / create jobs (global library) |
| GET/PUT/DELETE | `/jobs/{id}` | Get / update / delete a job |
| GET/POST | `/dags` | List / create DAGs |
| GET/PUT/DELETE | `/dags/{id}` | Get / update / delete a DAG |
| POST | `/dags/{id}/validate` | Validate DAG structure (cycle check) |
| POST | `/dags/{id}/runs` | Trigger a run |
| GET | `/dags/{id}/runs` | List runs for a DAG |
| GET | `/runs` | List all runs |
| GET | `/runs/{id}` | Get run detail + per-job states |
| POST | `/runs/{id}/cancel` | Cancel a running run |
| GET | `/runs/{id}/jobs/{jobId}/status` | Per-job status |
| GET | `/runs/{id}/jobs/{jobId}/logs` | Per-job logs/error |
| GET/PUT | `/settings/retention` | Get / update global retention setting |
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |

## Job handler types

The `handler_config` field on a job is a JSON object. Supported types:

| Type | Config keys | Description |
|------|-------------|-------------|
| `noop` | _(none)_ | Succeeds immediately. Useful for testing. |
| `script` | `command` (required), `timeout` (seconds, default 300) | Runs a shell command via subprocess. |

Example:
```json
{ "type": "script", "command": "python /jobs/etl.py", "timeout": 120 }
```

## Execution model

1. Triggering a run computes a topological sort of the DAG's jobs into **waves** (groups that can run in parallel).
2. Each wave executes jobs concurrently via a thread pool.
3. Per job: optional **input validation** → main **handler** → optional **output validation**. Any failure marks the job failed and skips downstream jobs.
4. If a job has `concurrency_enabled = false` (default), at most one run of that job executes at a time across all concurrent DAG runs.
5. The **scheduler** runs every `SCHEDULER_INTERVAL_SECONDS`, triggers any DAG whose cron schedule is due and has no recent run. Paused DAGs are skipped.

## Known gaps (vs. design)

- No per-job retry or backoff configuration.
- No per-job/per-run timeout in the job definition (script handler accepts a `timeout` in `handler_config`).
- Interrupted runs on engine restart are not automatically recovered.
- Auth is API-key only; JWT/OIDC and role-based access control (RBAC) are not yet implemented.
- No Prometheus metrics or distributed tracing.

## License

Proprietary / TBD
