"""Database engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.base import Base


def _get_engine():
    url = get_settings().database_url
    # SQLite: enable foreign keys and use connect_args for WAL
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        url,
        connect_args=connect_args,
        echo=get_settings().debug,
    )


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables. Prefer Alembic migrations in production."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency: yield a DB session. Use in FastAPI with Depends(get_db)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
