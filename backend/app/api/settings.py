"""Global settings routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.config import get_settings
from app.db.session import get_db
from app.repositories.global_setting_repository import GlobalSettingRepository
from app.schemas.settings import GlobalSettingResponse, RetentionSettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "/retention",
    response_model=GlobalSettingResponse,
    dependencies=[Depends(require_api_key)],
)
def get_retention(db: Session = Depends(get_db)):
    """Get effective retention setting (DB value or config default)."""
    repo = GlobalSettingRepository(db)
    db_val = repo.get_retention_days()
    effective = db_val if db_val is not None else get_settings().retention_days_default
    return {"key": "retention_days", "value": str(effective)}


@router.put(
    "/retention",
    response_model=GlobalSettingResponse,
    dependencies=[Depends(require_api_key)],
)
def update_retention(data: RetentionSettingUpdate, db: Session = Depends(get_db)):
    """Update retention setting. Takes effect immediately on next retention sweep."""
    repo = GlobalSettingRepository(db)
    setting = repo.set_value("retention_days", str(data.retention_days))
    db.commit()
    return {"key": setting.key, "value": setting.value}
