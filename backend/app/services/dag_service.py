"""DAG CRUD service with cycle detection and topological sort."""

from collections import defaultdict, deque

from sqlalchemy.orm import Session

from app.models.dag import DAG
from app.repositories.dag_repository import DAGRepository
from app.repositories.job_repository import JobRepository
from app.schemas.dag import DAGCreate, DAGUpdate, EdgeResponse


class DAGError(Exception):
    """Raised for invalid DAG operations (cycle, unknown job, etc.)."""


def _has_cycle(job_ids: set[str], edges: list[tuple[str, str]]) -> bool:
    """DFS-based cycle detection. Returns True if a cycle is found."""
    adj: dict[str, list[str]] = defaultdict(list)
    for f, t in edges:
        adj[f].append(t)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {j: WHITE for j in job_ids}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in adj.get(node, []):
            if neighbor not in color:
                color[neighbor] = WHITE
            if color[neighbor] == GRAY:
                return True
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(color[j] == WHITE and dfs(j) for j in job_ids)


def topological_waves(job_ids: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    """Return execution waves (groups of jobs that can run in parallel).

    Edge (A, B) means A must succeed before B runs.
    """
    in_degree: dict[str, int] = {j: 0 for j in job_ids}
    adj: dict[str, list[str]] = defaultdict(list)

    for f, t in edges:
        if f in in_degree and t in in_degree:
            adj[f].append(t)
            in_degree[t] += 1

    queue: deque[str] = deque(j for j in job_ids if in_degree[j] == 0)
    waves: list[list[str]] = []

    while queue:
        wave = list(queue)
        waves.append(wave)
        queue.clear()
        for job in wave:
            for neighbor in adj[job]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    return waves


def dag_to_dict(dag: DAG) -> dict:
    return {
        "id": dag.id,
        "name": dag.name,
        "description": dag.description,
        "schedule_cron": dag.schedule_cron,
        "schedule_timezone": dag.schedule_timezone,
        "paused": dag.paused,
        "retention_days_override": dag.retention_days_override,
        "edges": [
            EdgeResponse(from_job_id=e.from_job_id, to_job_id=e.to_job_id)
            for e in (dag.edges or [])
        ],
        "created_at": dag.created_at,
        "updated_at": dag.updated_at,
    }


class DAGService:
    def __init__(self, db: Session):
        self.dag_repo = DAGRepository(db)
        self.job_repo = JobRepository(db)
        self.db = db

    def _validate_edges(self, job_ids: list[str], edges: list[tuple[str, str]]) -> None:
        id_set = set(job_ids)
        for f, t in edges:
            if f not in id_set:
                raise DAGError(f"Edge references unknown job: {f}")
            if t not in id_set:
                raise DAGError(f"Edge references unknown job: {t}")
        if _has_cycle(id_set, edges):
            raise DAGError("DAG contains a cycle; cycles are not allowed")

    def create(self, data: DAGCreate) -> DAG:
        # Validate all referenced jobs exist
        for jid in data.job_ids:
            if not self.job_repo.exists(jid):
                raise DAGError(f"Job not found: {jid}")

        edge_tuples = [(e.from_job_id, e.to_job_id) for e in data.edges]
        self._validate_edges(data.job_ids, edge_tuples)

        dag = DAG(
            name=data.name,
            description=data.description,
            schedule_cron=data.schedule_cron,
            schedule_timezone=data.schedule_timezone,
            retention_days_override=data.retention_days_override,
        )
        self.dag_repo.add(dag)
        for f, t in edge_tuples:
            self.dag_repo.add_edge(dag.id, f, t)
        self.db.commit()
        self.db.refresh(dag)
        return dag

    def get(self, id: str) -> DAG | None:
        return self.dag_repo.get_with_edges(id)

    def list_all(self) -> list[DAG]:
        dags = self.dag_repo.list_all()
        # Eager-load edges for each DAG
        return [self.dag_repo.get_with_edges(d.id) for d in dags]

    def update(self, dag: DAG, data: DAGUpdate) -> DAG:
        if data.name is not None:
            dag.name = data.name
        if data.description is not None:
            dag.description = data.description
        if data.schedule_cron is not None:
            dag.schedule_cron = data.schedule_cron
        if data.schedule_timezone is not None:
            dag.schedule_timezone = data.schedule_timezone
        if data.paused is not None:
            dag.paused = data.paused
        if data.retention_days_override is not None:
            dag.retention_days_override = data.retention_days_override

        if data.job_ids is not None or data.edges is not None:
            # Get current state if partial update
            existing_edges = [(e.from_job_id, e.to_job_id) for e in (dag.edges or [])]
            job_ids = (
                data.job_ids
                if data.job_ids is not None
                else list({j for edge in existing_edges for j in edge})
            )
            edge_tuples = (
                [(e.from_job_id, e.to_job_id) for e in data.edges]
                if data.edges is not None
                else existing_edges
            )

            for jid in job_ids:
                if not self.job_repo.exists(jid):
                    raise DAGError(f"Job not found: {jid}")
            self._validate_edges(job_ids, edge_tuples)
            self.dag_repo.delete_edges(dag.id)
            for f, t in edge_tuples:
                self.dag_repo.add_edge(dag.id, f, t)

        self.db.commit()
        return self.dag_repo.get_with_edges(dag.id)

    def delete(self, dag: DAG) -> None:
        self.dag_repo.delete(dag)
        self.db.commit()

    def get_job_ids(self, dag: DAG) -> list[str]:
        """Return all unique job IDs referenced by this DAG's edges."""
        edges = self.dag_repo.get_edges(dag.id)
        ids = set()
        for f, t in edges:
            ids.add(f)
            ids.add(t)
        return list(ids)

    def get_execution_waves(self, dag: DAG) -> list[list[str]]:
        edges = self.dag_repo.get_edges(dag.id)
        job_ids = self.get_job_ids(dag)
        return topological_waves(job_ids, edges)
