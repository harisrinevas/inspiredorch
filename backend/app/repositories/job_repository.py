"""Job repository - global job library."""

from sqlalchemy.orm import Session

from app.models.job import Job
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, db: Session):
        super().__init__(db, Job)

    def list_all(self) -> list[Job]:
        return self.db.query(Job).order_by(Job.name).all()

    def list_by_ids(self, ids: list[str]) -> list[Job]:
        if not ids:
            return []
        return self.db.query(Job).filter(Job.id.in_(ids)).all()

    def exists(self, id: str) -> bool:
        return self.db.query(Job).filter(Job.id == id).first() is not None
