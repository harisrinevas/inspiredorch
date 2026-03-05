"""Job request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    handler_config: dict[str, Any] = Field(..., description='e.g. {"type": "script", "command": "echo hi"}')
    input_spec: Optional[dict[str, Any]] = None
    output_spec: Optional[dict[str, Any]] = None
    input_validation_enabled: bool = False
    output_validation_enabled: bool = False
    validator_config: Optional[dict[str, Any]] = None
    concurrency_enabled: bool = False


class JobUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    handler_config: Optional[dict[str, Any]] = None
    input_spec: Optional[dict[str, Any]] = None
    output_spec: Optional[dict[str, Any]] = None
    input_validation_enabled: Optional[bool] = None
    output_validation_enabled: Optional[bool] = None
    validator_config: Optional[dict[str, Any]] = None
    concurrency_enabled: Optional[bool] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: str
    name: str
    description: Optional[str]
    handler_config: dict[str, Any]
    input_spec: Optional[dict[str, Any]]
    output_spec: Optional[dict[str, Any]]
    input_validation_enabled: bool
    output_validation_enabled: bool
    validator_config: Optional[dict[str, Any]]
    concurrency_enabled: bool
    created_at: datetime
    updated_at: datetime
