# Data Pipeline Orchestrator — Design Document

**Status:** Implemented — containerised, running via `docker compose up`

This document describes the design of a simpler, abstraction-focused pipeline orchestrator (inspired by Airflow) with DAG-based jobs, optional validation steps, and a web UI. It is structured for enterprise-scale deployment with clear component boundaries, test strategy, and security posture.

---

## 1. High-Level Goals

| Goal | Description |
|------|-------------|
| **Simplicity** | Clear abstraction: jobs + dependencies only; no operator zoo. |
| **DAG-first** | Jobs and dependencies form a DAG; cycles are rejected. |
| **Validation** | Optional input validation and output validation per job. |
| **Enterprise** | Scalable, reliable, maintainable; suitable for production. |
| **Dual interface** | Web UI for day-to-day use; config/API for technical users. |

---

## 2. Core Abstractions

### 2.1 Job

- **Id** (unique), **name**, **description** (optional).
- **Handler**: What runs (e.g. script path, container image, or API endpoint). Abstract so we can support multiple execution backends later.
- **Optional steps** (each can be enabled/disabled via job config):
  - **Input validation**: Optional config (e.g. script path, schema URI). Runs before the main job; failure → job not run, downstream not triggered.
  - **Main execution**: The actual work.
  - **Output validation**: Optional config (e.g. script path, schema URI). Runs after the main job; failure → job marked failed, downstream not triggered.
- **Input/Output**: Optional metadata (e.g. expected input/output paths, schemas, or key-value params). Used by validation and for documentation/lineage.
- **Concurrency**: Per-job flag to **enable** or **disable** concurrent runs of that job. When enabled, max parallel runs for that job are determined by the orchestrator from system capacity (see §4.4).

### 2.2 DAG (Pipeline)

- **Id**, **name**, **description**.
- **Vertices**: Jobs from the **global job library** (DAG references job ids).
- **Edges**: Dependencies (A → B means “B depends on A”; A must succeed before B runs).
- **Invariants**: No cycles. One job can appear in multiple DAGs (global job library + DAG = graph over job ids).
- **Trigger**: Manual (UI/API) or schedule (cron-like). One “run” = one DAG execution (run id, timestamps, status per job).

### 2.3 Run (DAG Execution)

- **Run id**, **DAG id**, **trigger time**, **triggered by** (user/scheduler).
- **Status**: e.g. `pending` | `running` | `success` | `failed` | `cancelled`.
- **Per-job status**: For each job in the DAG: `pending` | `input_validation` | `running` | `output_validation` | `success` | `failed` | `skipped` | `cancelled`.
- **Artifacts**: Optional references to input/output (e.g. paths, object store keys) and validation results for auditing.

---

## 3. Component Breakdown

We split the system into **six main components** plus cross-cutting concerns. Each component has a single responsibility and clear boundaries.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Web UI (Frontend)                              │
│  DAG editor, run monitor, job config, validation config, audit           │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Gateway / BFF                              │
│  REST (and optional OpenAPI); auth, rate limit, request validation       │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│  DAG / Job       │    │  Execution            │    │  Scheduler           │
│  Management      │    │  Engine               │    │  Service             │
│  (CRUD, validate)│    │  (run jobs, validate) │    │  (cron, trigger run) │
└──────────────────┘    └──────────────────────┘    └──────────────────────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Metadata & State Store                            │
│  DAGs, jobs, runs, job states, audit logs                                │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Execution Runtime (Workers)                       │
│  Runs job handlers (e.g. containers, processes, future: serverless)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Designs

### 4.1 Web UI (Frontend)

**Responsibility:** Single place for users to manage pipelines and monitor runs.

**Features:**

- **DAG canvas**: Visual DAG editor — add/remove jobs, draw dependencies, no cycles (validated on save).
- **Job config**: Form for job name, handler, optional input/output metadata, optional validator config (input/output validation with script/schema etc.), and concurrency enable/disable.
- **Run dashboard**: List runs (filter by DAG, date, status); drill into a run to see per-job status and logs.
- **“Under the hood”**: Collapsible/advanced section or separate “Config” view for technical users (raw YAML/JSON of DAG and job definitions, env vars, timeouts, retries).

**Design choices:**

- **Tech**: **React** SPA + REST API for responsiveness and API-first use.
- **State**: Server is source of truth; UI fetches via API; no business logic in UI beyond validation for UX.
- **Access**: All actions go through API with auth; no direct DB access from browser.
- **Production serving**: Vite builds a static `dist/`. An **nginx** container serves the static files and reverse-proxies `/api/* → backend:8000/*` (the `/api` prefix is stripped before forwarding, mirroring the Vite dev proxy). SPA routing is handled by an `index.html` fallback (`try_files`).

**Deliverables (per phase):** UI component; E2E tests against real API (or mock); accessibility and basic security (no secrets in client, CSP).

---

### 4.2 API Gateway / Backend-for-Frontend (BFF)

**Responsibility:** Single entry point for UI and API clients; auth, authorization, rate limiting, input validation.

**Endpoints (conceptual):**

- **DAGs:** `GET/POST/PUT/DELETE /dags`, `GET /dags/:id`, `POST /dags/:id/validate`.
- **Jobs:** `GET/POST/PUT/DELETE /jobs` (global job library; DAGs reference job ids).
- **Runs:** `POST /dags/:id/runs`, `GET /runs`, `GET /runs/:id`, `POST /runs/:id/cancel`.
- **Run job status / logs:** `GET /runs/:id/jobs/:jobId/status`, `GET /runs/:id/jobs/:jobId/logs`.
- **Health:** `GET /health`, `GET /ready`.

**Design choices:**

- **API style:** REST with JSON; OpenAPI 3 spec for all endpoints (enables codegen and security review).
- **Auth:** Start with API keys or JWT; later add OIDC/SSO. Every request authenticated; authorization by “role” (e.g. viewer, operator, admin).
- **Validation:** Strict request validation (schema); reject invalid payloads with 400.
- **Idempotency:** For “trigger run”, optional idempotency key to avoid duplicate runs.

**Deliverables:** OpenAPI spec; implementation; contract tests; security (auth, input validation, no sensitive data in responses).

---

### 4.3 DAG / Job Management Service

**Responsibility:** CRUD for DAGs and jobs; dependency graph validation (no cycles); persistence of definitions.

**Core logic:**

- **Store:** DAG and job definitions (versioned if we want history; at minimum current snapshot).
- **Validation:** On create/update, build in-memory graph and check for cycles (e.g. DFS); reject if cycle detected.
- **Consistency:** optional: “job library” vs “DAG-scoped jobs” (design decision: one global job set and DAGs reference them, or jobs defined per DAG — recommend global jobs + DAG = graph over job ids).

**Data model (logical):**

- **Job:** id, name, description, handler_config, input_spec, output_spec, input_validation_enabled, output_validation_enabled, **validator_config** (optional: script path, schema URI, etc. for input/output validators), **concurrency_enabled** (boolean; when true, orchestrator caps parallel runs by system capacity).
- **DAG:** id, name, description, job_ids, edges (list of (from_job_id, to_job_id)).
- **Versioning:** Optional `version` or `updated_at` for optimistic locking.

**Deliverables:** Service module/package; unit tests (cycle detection, CRUD); integration tests with Metadata Store; no secrets in definitions (or encrypted at rest if needed).

---

### 4.4 Execution Engine

**Responsibility:** Execute a single DAG run: resolve order (topological sort), run jobs respecting dependencies, run input/output validation steps, persist state.

**Flow for one run:**

1. Load DAG and run definition; compute topological order.
2. Initialize all job states to `pending`.
3. For each wave (jobs with all upstream deps satisfied):
   - For each job: if input validation enabled → run input validator; on failure mark job failed and skip downstream.
   - Run main handler; on failure mark job failed and skip downstream.
   - If output validation enabled → run output validator; on failure mark job failed and skip downstream.
4. Persist state after each job (or batch) so that restarts can resume (if we design for resume).

**Design choices:**

- **Orchestrator vs workers:** Engine is the “orchestrator”; it decides *what* to run and *when*. Actual execution can be in-process, subprocess, or remote workers (queue-based). Recommend: engine enqueues “run job X for run Y”; workers pull and execute; engine updates state from worker results. This gives scalability and isolation.
- **Concurrency (job-level):** Each job has a **concurrency_enabled** flag. When **disabled**, at most one run of that job executes at a time (across all DAG runs). When **enabled**, the orchestrator limits parallel runs of that job based on **system capacity** (e.g. CPU cores, processor count, or configurable cap derived from hardware/software limits). The engine discovers or is configured with these limits at startup and enforces them when scheduling.
- **Single-process constraint:** The engine uses an in-process `_job_locks` dict for per-job concurrency control. `uvicorn` must therefore be run with `--workers 1`. Multiple workers would not share lock state.
- **Retries:** Configurable per-job retry (count, backoff); optional dead-letter or alert on final failure.
- **Timeouts:** Per-job and optional per-run timeout.
- **Idempotency:** Same run id never executed twice; idempotency in worker if needed for at-least-once.

**Handler types (implemented):**

| Type | Behaviour |
|------|-----------|
| `noop` | Succeeds immediately; useful for testing. |
| `script` | Runs `handler_config.command` via shell subprocess (`subprocess.run`). |
| `container` | Runs a command inside a Docker container (see §4.7). |

**Deliverables:** Engine core (topological execution, state transitions); worker interface (contract); unit tests (mock store and worker); integration test with real queue and one dummy job.

---

### 4.5 Scheduler Service

**Responsibility:** Trigger DAG runs on a schedule (cron-like) and optionally honor “trigger once” or time windows.

**Design:**

- **Schedules:** Stored per DAG (e.g. cron expression, timezone). Optional: “paused” flag.
- **Scheduler process:** Wakes on tick (e.g. every minute), evaluates which DAGs are due, creates run records and hands off to Execution Engine (e.g. by enqueueing “start run X”).
- **Overlap policy:** If a DAG run is still running when next schedule hits: skip, or queue (max queued per DAG cap), or parallel (configurable). Recommend: default “skip” or “queue with cap” to avoid thundering herd.

**Deliverables:** Scheduler service; unit tests (cron evaluation, overlap policy); integration test with mock Execution Engine; no direct DB writes from scheduler for job state (only “create run” and “request execution”).

---

### 4.6 Metadata & State Store

**Responsibility:** Persist DAGs, jobs, runs, per-job run state, and optionally audit logs.

**Design choices:**

- **Storage:** SQL DB (e.g. PostgreSQL) for structured data (DAGs, jobs, runs, job_run_states); optional separate store for logs (e.g. object store or log aggregator). Recommendation: start with PostgreSQL; add blob/log storage if needed.
- **Default (containerised):** **SQLite** at absolute path `/data/orchestrator.db` written to a named Docker volume (`db_data`), so data persists across container restarts. PostgreSQL is available as an opt-in via `docker compose --profile postgres up` with `DATABASE_URL` set to the postgres service.
- **Migrations:** Managed by **Alembic**. In the containerised setup, `alembic upgrade head` runs automatically in `backend/entrypoint.sh` before uvicorn starts.
- **Schema:** Tables aligned to DAG, Job, Run, JobRunState (run_id, job_id, status, started_at, finished_at, error_message, logs_ref). Retention policy stored globally and/or per DAG (see below).
- **Consistency:** Use transactions for run creation and state updates; avoid dual-writes (single writer per run state where possible).
- **Retention:** **Configurable** with a **default of 90 days**. Stored at global level and overridable per DAG. **Modifiable at any time**; when the retention value is changed (global or per DAG), the new value **takes effect immediately** (next retention sweep applies the new N days). Retention job/sweep deletes or archives runs older than N days; implementation must use the current retention setting at execution time, not a cached value.

**Deliverables:** Schema (migrations); repository layer used by DAG/Job service and Execution Engine; backup/restore and retention strategy documented.

---

### 4.7 Execution Runtime (Workers)

**Responsibility:** Execute a single job (and optionally its validators) in a safe, isolated way.

**Design:**

- **Contract:** Worker receives “job run id, job id, handler config, input refs”; runs handler; reports success/failure, logs, output refs. Validators can be “same contract” with a different handler type.
- **Isolation:** Prefer containers (e.g. one container per job run) or at least process isolation; resource limits (CPU, memory).
- **Environments:** Support different runtimes (e.g. Python, Node, shell, container image) via a small adapter layer so the worker can invoke the right runner.
- **Secrets:** Not in job definition; injected via env or mounted volume from a secret store (e.g. env vars from a vault). UI never sees raw secrets.

**Container handler (implemented):**

The `container` handler type in the execution engine runs a command inside a short-lived Docker container using the Docker SDK (`docker>=7.0.0`).

`handler_config` fields:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | yes | — | `”container”` |
| `image` | yes | — | Docker image to run (pulled automatically if not present) |
| `command` | yes | — | Command to execute inside the container |
| `timeout` | no | `300` | Seconds before the wait times out |
| `environment` | no | `{}` | Dict of env vars injected into the container |
| `volumes` | no | `[]` | List of `”host:container[:mode]”` volume bind strings |

**Behaviour:** The backend connects to the Docker daemon via the mounted socket (`/var/run/docker.sock`). The container runs on the **host** daemon (not nested inside the backend container). After the command completes, stdout+stderr are captured as logs and the container is removed. On timeout or error, the container is forcibly removed in a `finally` block.

**`DOCKER_HOST` / `docker_host` config:** The daemon URL can be overridden via the `DOCKER_HOST` environment variable or `docker_host` in `Settings` (e.g. for remote Docker contexts).

**Example `handler_config`:**
```json
{
  “type”: “container”,
  “image”: “python:3.11-slim”,
  “command”: “python -c \”print('hello from container')\””,
  “timeout”: 60,
  “environment”: {“MY_VAR”: “value”},
  “volumes”: [“/host/data:/data:ro”]
}
```

**Deliverables:** Worker service(s); adapter for at least one runtime (e.g. Python script or container); tests (run dummy job, timeout, failure); security (no arbitrary code from UI without validation/sandbox).

---

## 5. Cross-Cutting Concerns

### 5.1 Security

- **Authentication:** All API and UI calls authenticated (API key or JWT); scheduler runs as a system identity.
- **Authorization:** Roles (e.g. viewer, operator, admin); RBAC on DAGs/jobs (who can edit, who can trigger, who can see logs).
- **Secrets:** Never store in DAG/job JSON; use secret manager; inject at runtime into workers.
- **Input validation:** Strict validation on all API inputs and on job/validator configs to avoid injection (e.g. no eval of user strings as code unless in a sandbox).
- **Supply chain:** Dependencies (e.g. Python/Node packages, container images) tracked and scanned (see below).
- **Network:** API over HTTPS; internal services on private network; workers can reach only allowed endpoints if needed.

### 5.2 Observability

- **Logging:** Structured logs (JSON); correlation id per request and per run.
- **Metrics:** Counts and latencies for runs (started, succeeded, failed), job duration, queue depth; export to Prometheus or equivalent.
- **Tracing:** Optional distributed trace (run id → job run ids) for debugging.
- **Alerting:** On run failure or scheduler issues (integrate with existing alerting channel).

### 5.3 Reliability

- **Idempotency:** Run creation and “start run” idempotent where possible.
- **State machine:** Clear states and transitions for runs and job runs; no ambiguous states.
- **Recovery:** On engine restart, resume or fail open runs according to policy (e.g. mark “interrupted” and allow retry).
- **Backup:** DB and critical config backed up; documented restore procedure.

---

## 6. Implementation & Deployment Plan

**Order of implementation (per component):**

1. **Metadata & State Store** — schema and repository layer; no UI. ✅
2. **DAG / Job Management Service** — CRUD + cycle validation; expose via API only (no UI yet). ✅
3. **API Gateway / BFF** — REST + auth + validation; wire to DAG/Job and later to Engine. ✅
4. **Execution Engine + Workers** — core execution; `noop`, `script`, and `container` handler types. ✅
5. **Scheduler Service** — cron trigger; wire to Engine and Store. ✅
6. **Web UI** — DAG editor, run dashboard, job config, “under the hood” view. ✅
7. **Containerisation** — Docker images for backend and frontend; `docker compose up` startup; SQLite default with named volume; PostgreSQL opt-in profile; container handler via Docker socket. ✅

For each component:

- **Implement** according to this design.
- **Test:** Unit tests (high coverage for core logic), integration tests (with real DB/queue where needed), contract tests for API.
- **Security:** Dependency and container image vulnerability scans; static analysis (SAST); no hardcoded secrets; auth on every endpoint.
- **Deploy** one component at a time (e.g. API + DAG service first; then Engine + Workers; then Scheduler; then UI), and **test** after each step (smoke + critical paths).

**Environments:** Recommend at least `dev` and `staging` before production; same code, different config and secrets.

---

## 7. Testing Strategy Summary

| Layer | What to test |
|-------|------------------|
| **Unit** | Cycle detection, topological sort, state transitions, validation rules, cron parsing. |
| **Integration** | DAG CRUD + store; run creation and state updates; worker execution and callback. |
| **Contract** | API request/response shapes (OpenAPI + examples). |
| **E2E** | Create DAG via API → trigger run → verify job states and final run status (with dummy job). |
| **Security** | Auth required; no secrets in responses; dependency and image scans; SAST. |

---

## 8. Open Decisions (for your input)

1. **Job scope:** Global job library (reusable across DAGs) vs jobs defined per DAG? Recommendation: global jobs + DAG as graph over job ids.
2. **Validator definition:** Validators as “special job type” vs separate config (e.g. script path or schema URI). Recommendation: separate config (script or schema) per job to keep abstraction simple.
3. **Run persistence:** Full history forever vs retention (e.g. 90 days) with optional archive to cold storage.
4. **Concurrency:** Max parallel runs per DAG and max parallel job runs globally (to protect resources).
5. **Tech stack:** Language and framework for API and workers (e.g. Python/FastAPI, Go, Node). Choice affects deployment and hiring.

---

## 9. Sign-off

Decisions locked and fully implemented. See §10 for how to run.

---

## 10. Deployment

### Docker Compose (recommended)

```bash
# Default — SQLite, everything in one command
docker compose up --build

# PostgreSQL opt-in
POSTGRES_PASSWORD=secret \
DATABASE_URL=postgresql+psycopg2://orchestrator:secret@postgres:5432/orchestrator \
docker compose --profile postgres up --build
```

| URL | Service |
|-----|---------|
| `http://localhost` | React UI (nginx) |
| `http://localhost/api/health` | Backend health (via nginx proxy) |
| `http://localhost:8000/health` | Backend health (direct) |

### Services (`docker-compose.yml`)

| Service | Image | Notes |
|---------|-------|-------|
| `backend` | `./backend` (python:3.11-slim) | Runs `alembic upgrade head` then uvicorn on port 8000 |
| `frontend` | `./frontend` (node:20 → nginx:alpine) | nginx serves `dist/`, proxies `/api/` to backend |
| `postgres` | `postgres:16-alpine` | Profile `postgres`; opt-in only |

### Volumes

| Volume | Purpose |
|--------|---------|
| `db_data` | SQLite file at `/data/orchestrator.db`; persists across restarts |
| `pg_data` | PostgreSQL data directory (when postgres profile is active) |

### Docker socket

The backend container mounts `/var/run/docker.sock` from the host. This allows the `container` handler to spawn job containers directly on the host Docker daemon (no nesting). On Windows, Docker Desktop exposes the socket to WSL2 containers at the same path.

### Key environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:////data/orchestrator.db` | DB connection string |
| `API_KEY` | _(none)_ | If set, all API requests require `X-Api-Key` header |
| `SCHEDULER_INTERVAL_SECONDS` | `60` | How often the scheduler polls for due DAGs |
| `DOCKER_HOST` | _(socket)_ | Override Docker daemon URL for container handler |

---

*Document version: 2.0 — Implemented*
