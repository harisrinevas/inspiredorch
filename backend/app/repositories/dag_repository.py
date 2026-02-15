"""DAG and DAGEdge repository."""

from sqlalchemy.orm import Session, joinedload

from app.models.dag import DAG, DAGEdge
from app.repositories.base import BaseRepository


class DAGRepository(BaseRepository[DAG]):
    def __init__(self, db: Session):
        super().__init__(db, DAG)

    def list_all(self) -> list[DAG]:
        return self.db.query(DAG).order_by(DAG.name).all()

    def get_with_edges(self, id: str) -> DAG | None:
        return (
            self.db.query(DAG)
            .options(joinedload(DAG.edges))
            .filter(DAG.id == id)
            .first()
        )

    def get_edges(self, dag_id: str) -> list[tuple[str, str]]:
        """Return list of (from_job_id, to_job_id) for the DAG."""
        rows = (
            self.db.query(DAGEdge.from_job_id, DAGEdge.to_job_id)
            .filter(DAGEdge.dag_id == dag_id)
            .all()
        )
        return [(r.from_job_id, r.to_job_id) for r in rows]

    def add_edge(self, dag_id: str, from_job_id: str, to_job_id: str) -> DAGEdge:
        edge = DAGEdge(dag_id=dag_id, from_job_id=from_job_id, to_job_id=to_job_id)
        self.db.add(edge)
        self.db.flush()
        return edge

    def delete_edges(self, dag_id: str) -> int:
        return self.db.query(DAGEdge).filter(DAGEdge.dag_id == dag_id).delete()
