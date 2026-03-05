"""Settings request/response schemas."""

from pydantic import BaseModel, Field


class GlobalSettingResponse(BaseModel):
    key: str
    value: str


class RetentionSettingUpdate(BaseModel):
    retention_days: int = Field(..., ge=1, description="Retention in days; applies immediately to next sweep")
