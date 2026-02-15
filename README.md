# Data Pipeline Orchestrator

A simpler, DAG-based pipeline orchestrator with optional input/output validation, global job library, and web UI. See [DESIGN.md](DESIGN.md) for architecture and decisions.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend:** React (to be added)
- **Install target:** Linux / WSL

## Project structure

```
Orchestrator/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # REST routes (added with API component)
│   │   ├── core/            # Config, security
│   │   ├── db/              # Database base, session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   └── services/       # Business logic (added with services)
│   ├── tests/
│   ├── alembic/             # DB migrations
│   └── requirements.txt
├── frontend/                # React UI (to be added)
├── docs/                    # Additional documentation
├── scripts/                 # Install and utility scripts
├── DESIGN.md
└── README.md
```

## Implementation status

| Component | Status |
|-----------|--------|
| 1. Metadata & State Store | In progress |
| 2. DAG / Job Management Service | Pending |
| 3. API Gateway / BFF | Pending |
| 4. Execution Engine + Workers | Pending |
| 5. Scheduler Service | Pending |
| 6. Web UI | Pending |

## Quick start (backend)

Requires Python 3.11+ and PostgreSQL (or SQLite for local dev).

```bash
cd backend
python -m venv .venv
# Linux/WSL: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # edit with your DB URL
alembic upgrade head
uvicorn app.main:app --reload
```

Health: `GET http://localhost:8000/health`

## License

Proprietary / TBD
