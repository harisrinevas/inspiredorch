"""Pytest fixtures: in-memory SQLite DB and session."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.base import Base
from app.models import Job, DAG, DAGEdge, Run, JobRunState, GlobalSetting  # noqa: F401


@pytest.fixture(scope="function")
def engine():
    """In-memory SQLite engine per test."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )


@pytest.fixture(scope="function")
def tables(engine):
    """Create all tables in the test engine."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine, tables) -> Session:
    """Session for tests. Rolls back after each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
