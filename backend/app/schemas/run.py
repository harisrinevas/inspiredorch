"""Run request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TriggerRunRequest(BaseModel):
    triggered_by: Optional[str] = "api"


class JobRunStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    run_id: str
    job_id: str
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_message: Optional[str]
    logs_ref: Optional[str]


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    dag_id: str
    trigger_time: datetime
    triggered_by: Optional[str]
    status: str
    created_at: datetime
    job_run_states: list[JobRunStateResponse] = []


class RunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    dag_id: str
    trigger_time: datetime
    triggered_by: Optional[str]
    status: str
    created_at: datetime
