"""DAG request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EdgeInput(BaseModel):
    from_job_id: str
    to_job_id: str


class EdgeResponse(BaseModel):
    from_job_id: str
    to_job_id: str


class DAGCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    job_ids: list[str] = Field(default_factory=list, description="Jobs included in this DAG")
    edges: list[EdgeInput] = Field(default_factory=list, description="Dependency edges")
    schedule_cron: Optional[str] = Field(None, description="Cron expression, e.g. '0 * * * *'")
    schedule_timezone: Optional[str] = Field(None, description="Timezone name, e.g. 'UTC'")
    retention_days_override: Optional[int] = Field(None, ge=1)


class DAGUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    job_ids: Optional[list[str]] = None
    edges: Optional[list[EdgeInput]] = None
    schedule_cron: Optional[str] = None
    schedule_timezone: Optional[str] = None
    paused: Optional[bool] = None
    retention_days_override: Optional[int] = Field(None, ge=1)


class DAGResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    name: str
    description: Optional[str]
    schedule_cron: Optional[str]
    schedule_timezone: Optional[str]
    paused: bool
    retention_days_override: Optional[int]
    edges: list[EdgeResponse]
    created_at: datetime
    updated_at: datetime
