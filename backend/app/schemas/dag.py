"""DAG request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EdgeInput(BaseModel):
    from_job_id: str
    to_job_id: str


class EdgeResponse(BaseModel):
    from_job_id: str
    to_job_id: str


class DAGCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    job_ids: list[str] = Field(default_factory=list, description="Jobs included in this DAG")
    edges: list[EdgeInput] = Field(default_factory=list, description="Dependency edges")
    schedule_cron: str | None = Field(None, description="Cron expression, e.g. '0 * * * *'")
    schedule_timezone: str | None = Field(None, description="Timezone name, e.g. 'UTC'")
    retention_days_override: int | None = Field(None, ge=1)


class DAGUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    job_ids: list[str] | None = None
    edges: list[EdgeInput] | None = None
    schedule_cron: str | None = None
    schedule_timezone: str | None = None
    paused: bool | None = None
    retention_days_override: int | None = Field(None, ge=1)


class DAGResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    name: str
    description: str | None
    schedule_cron: str | None
    schedule_timezone: str | None
    paused: bool
    retention_days_override: int | None
    edges: list[EdgeResponse]
    created_at: datetime
    updated_at: datetime
