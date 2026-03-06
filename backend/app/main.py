"""FastAPI application — Data Pipeline Orchestrator."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, start scheduler. Shutdown: stop scheduler."""
    settings = get_settings()
    init_db()

    from app.services.scheduler_service import SchedulerService

    scheduler = SchedulerService(interval_seconds=settings.scheduler_interval_seconds)
    scheduler.start()
    app.state.scheduler = scheduler

    yield

    scheduler.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="DAG-based data pipeline orchestrator with job library, validation, and scheduling.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.dags import router as dags_router
    from app.api.jobs import router as jobs_router
    from app.api.runs import router as runs_router
    from app.api.settings import router as settings_router

    app.include_router(jobs_router)
    app.include_router(dags_router)
    app.include_router(runs_router)
    app.include_router(settings_router)

    @app.get("/health", tags=["system"])
    def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["system"])
    def ready():
        return {"status": "ready"}

    return app


app = create_app()
