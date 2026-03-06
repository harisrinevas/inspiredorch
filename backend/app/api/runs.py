"""Run management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.db.session import get_db
from app.schemas.run import JobRunStateResponse, RunListItem, RunResponse
from app.services.run_service import RunService, job_state_to_dict, run_list_item_to_dict, run_to_dict

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunListItem], dependencies=[Depends(require_api_key)])
def list_runs(limit: int = 100, db: Session = Depends(get_db)):
    svc = RunService(db)
    runs = svc.list_all(limit=limit)
    return [run_list_item_to_dict(r) for r in runs]


@router.get("/{run_id}", response_model=RunResponse, dependencies=[Depends(require_api_key)])
def get_run(run_id: str, db: Session = Depends(get_db)):
    svc = RunService(db)
    run = svc.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_to_dict(run)


@router.post("/{run_id}/cancel", status_code=status.HTTP_200_OK, dependencies=[Depends(require_api_key)])
def cancel_run(run_id: str, db: Session = Depends(get_db)):
    svc = RunService(db)
    run = svc.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    cancelled = svc.cancel_run(run)
    if not cancelled:
        raise HTTPException(status_code=409, detail=f"Run is already in terminal state: {run.status}")
    return {"status": "cancelled", "run_id": run_id}


@router.get("/{run_id}/jobs/{job_id}/status", response_model=JobRunStateResponse, dependencies=[Depends(require_api_key)])
def get_job_run_status(run_id: str, job_id: str, db: Session = Depends(get_db)):
    from app.repositories.job_run_state_repository import JobRunStateRepository
    repo = JobRunStateRepository(db)
    state = repo.get_by_run_and_job(run_id, job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job run state not found")
    return job_state_to_dict(state)


@router.get("/{run_id}/jobs/{job_id}/logs", dependencies=[Depends(require_api_key)])
def get_job_run_logs(run_id: str, job_id: str, db: Session = Depends(get_db)):
    from app.repositories.job_run_state_repository import JobRunStateRepository
    repo = JobRunStateRepository(db)
    state = repo.get_by_run_and_job(run_id, job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job run state not found")
    return {
        "run_id": run_id,
        "job_id": job_id,
        "logs": state.logs,
        "logs_ref": state.logs_ref,
        "error_message": state.error_message,
    }
