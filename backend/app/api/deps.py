"""FastAPI dependencies: auth, DB session."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db


def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require API key if one is configured. No-op in dev mode (api_key=None)."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
