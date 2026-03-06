"""DAG CRUD and trigger routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.db.session import get_db
from app.schemas.dag import DAGCreate, DAGResponse, DAGUpdate
from app.schemas.run import RunResponse, TriggerRunRequest
from app.services.dag_service import DAGError, DAGService, dag_to_dict
from app.services.execution_engine import ExecutionEngine
from app.services.run_service import RunService, run_to_dict

router = APIRouter(prefix="/dags", tags=["dags"])


@router.get("", response_model=list[DAGResponse], dependencies=[Depends(require_api_key)])
def list_dags(db: Session = Depends(get_db)):
    svc = DAGService(db)
    return [dag_to_dict(d) for d in svc.list_all()]


@router.post(
    "",
    response_model=DAGResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_dag(data: DAGCreate, db: Session = Depends(get_db)):
    svc = DAGService(db)
    try:
        dag = svc.create(data)
    except DAGError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return dag_to_dict(dag)


@router.get("/{dag_id}", response_model=DAGResponse, dependencies=[Depends(require_api_key)])
def get_dag(dag_id: str, db: Session = Depends(get_db)):
    svc = DAGService(db)
    dag = svc.get(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")
    return dag_to_dict(dag)


@router.put("/{dag_id}", response_model=DAGResponse, dependencies=[Depends(require_api_key)])
def update_dag(dag_id: str, data: DAGUpdate, db: Session = Depends(get_db)):
    svc = DAGService(db)
    dag = svc.get(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")
    try:
        dag = svc.update(dag, data)
    except DAGError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return dag_to_dict(dag)


@router.delete(
    "/{dag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_dag(dag_id: str, db: Session = Depends(get_db)):
    svc = DAGService(db)
    dag = svc.get(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")
    svc.delete(dag)


@router.post("/{dag_id}/validate", dependencies=[Depends(require_api_key)])
def validate_dag(dag_id: str, db: Session = Depends(get_db)):
    """Validate DAG structure (no cycles, all jobs exist). Returns validation result."""
    svc = DAGService(db)
    dag = svc.get(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")
    try:
        waves = svc.get_execution_waves(dag)
        return {"valid": True, "execution_waves": waves}
    except DAGError as exc:
        return {"valid": False, "error": str(exc)}


@router.post(
    "/{dag_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def trigger_run(dag_id: str, body: TriggerRunRequest = None, db: Session = Depends(get_db)):
    """Trigger a new run for this DAG."""
    dag_svc = DAGService(db)
    dag = dag_svc.get(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")

    job_ids = dag_svc.get_job_ids(dag)
    triggered_by = (body.triggered_by if body else None) or "api"

    run_svc = RunService(db)
    run = run_svc.create_run(dag_id, job_ids, triggered_by=triggered_by)

    engine = ExecutionEngine()
    engine.trigger(run.id)

    return run_to_dict(run)


@router.get("/{dag_id}/runs", response_model=list, dependencies=[Depends(require_api_key)])
def list_dag_runs(dag_id: str, limit: int = 50, db: Session = Depends(get_db)):
    dag_svc = DAGService(db)
    if not dag_svc.get(dag_id):
        raise HTTPException(status_code=404, detail="DAG not found")
    run_svc = RunService(db)
    runs = run_svc.list_by_dag(dag_id, limit=limit)
    from app.services.run_service import run_list_item_to_dict

    return [run_list_item_to_dict(r) for r in runs]
