"""Job CRUD service."""

import json

from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate, JobUpdate


def _parse(val: str | None) -> dict | None:
    if val is None:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return {}


def job_to_dict(job: Job) -> dict:
    return {
        "id": job.id,
        "name": job.name,
        "description": job.description,
        "handler_config": _parse(job.handler_config) or {},
        "input_spec": _parse(job.input_spec),
        "output_spec": _parse(job.output_spec),
        "input_validation_enabled": job.input_validation_enabled,
        "output_validation_enabled": job.output_validation_enabled,
        "validator_config": _parse(job.validator_config),
        "concurrency_enabled": job.concurrency_enabled,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


class JobService:
    def __init__(self, db: Session):
        self.repo = JobRepository(db)
        self.db = db

    def create(self, data: JobCreate) -> Job:
        job = Job(
            name=data.name,
            description=data.description,
            handler_config=json.dumps(data.handler_config),
            input_spec=json.dumps(data.input_spec) if data.input_spec is not None else None,
            output_spec=json.dumps(data.output_spec) if data.output_spec is not None else None,
            input_validation_enabled=data.input_validation_enabled,
            output_validation_enabled=data.output_validation_enabled,
            validator_config=json.dumps(data.validator_config)
            if data.validator_config is not None
            else None,
            concurrency_enabled=data.concurrency_enabled,
        )
        self.repo.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, id: str) -> Job | None:
        return self.repo.get(id)

    def list_all(self) -> list[Job]:
        return self.repo.list_all()

    def update(self, job: Job, data: JobUpdate) -> Job:
        if data.name is not None:
            job.name = data.name
        if data.description is not None:
            job.description = data.description
        if data.handler_config is not None:
            job.handler_config = json.dumps(data.handler_config)
        if data.input_spec is not None:
            job.input_spec = json.dumps(data.input_spec)
        if data.output_spec is not None:
            job.output_spec = json.dumps(data.output_spec)
        if data.input_validation_enabled is not None:
            job.input_validation_enabled = data.input_validation_enabled
        if data.output_validation_enabled is not None:
            job.output_validation_enabled = data.output_validation_enabled
        if data.validator_config is not None:
            job.validator_config = json.dumps(data.validator_config)
        if data.concurrency_enabled is not None:
            job.concurrency_enabled = data.concurrency_enabled
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job: Job) -> None:
        self.repo.delete(job)
        self.db.commit()
