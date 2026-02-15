"""FastAPI application - shell for Component 1 (Metadata & State Store)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure DB exists (migrations preferred in production)."""
    # init_db()  # uncomment to create tables without Alembic
    yield
    # shutdown


app = FastAPI(
    title=get_settings().app_name,
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    """Health check for deploy and scripts."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: DB connectivity could be checked here."""
    return {"status": "ready"}
