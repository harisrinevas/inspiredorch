"""Job request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    handler_config: dict[str, Any] = Field(
        ..., description='e.g. {"type": "script", "command": "echo hi"}'
    )
    input_spec: dict[str, Any] | None = None
    output_spec: dict[str, Any] | None = None
    input_validation_enabled: bool = False
    output_validation_enabled: bool = False
    validator_config: dict[str, Any] | None = None
    concurrency_enabled: bool = False


class JobUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    handler_config: dict[str, Any] | None = None
    input_spec: dict[str, Any] | None = None
    output_spec: dict[str, Any] | None = None
    input_validation_enabled: bool | None = None
    output_validation_enabled: bool | None = None
    validator_config: dict[str, Any] | None = None
    concurrency_enabled: bool | None = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    name: str
    description: str | None
    handler_config: dict[str, Any]
    input_spec: dict[str, Any] | None
    output_spec: dict[str, Any] | None
    input_validation_enabled: bool
    output_validation_enabled: bool
    validator_config: dict[str, Any] | None
    concurrency_enabled: bool
    created_at: datetime
    updated_at: datetime
