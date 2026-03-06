"""Job CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.db.session import get_db
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.job_service import JobService, job_to_dict

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse], dependencies=[Depends(require_api_key)])
def list_jobs(db: Session = Depends(get_db)):
    svc = JobService(db)
    return [job_to_dict(j) for j in svc.list_all()]


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_job(data: JobCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.create(data)
    return job_to_dict(job)


@router.get("/{job_id}", response_model=JobResponse, dependencies=[Depends(require_api_key)])
def get_job(job_id: str, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_dict(job)


@router.put("/{job_id}", response_model=JobResponse, dependencies=[Depends(require_api_key)])
def update_job(job_id: str, data: JobUpdate, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job = svc.update(job, data)
    return job_to_dict(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    svc.delete(job)
