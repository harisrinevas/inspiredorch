"""Run request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TriggerRunRequest(BaseModel):
    triggered_by: str | None = "api"


class JobRunStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    run_id: str
    job_id: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    logs: str | None
    logs_ref: str | None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    dag_id: str
    trigger_time: datetime
    triggered_by: str | None
    status: str
    created_at: datetime
    job_run_states: list[JobRunStateResponse] = []


class RunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    dag_id: str
    trigger_time: datetime
    triggered_by: str | None
    status: str
    created_at: datetime
