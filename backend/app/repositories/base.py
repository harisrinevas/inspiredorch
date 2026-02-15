"""Base repository with common CRUD."""

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic repository. Subclass per entity."""

    def __init__(self, db: Session, model_class: type[ModelT]):
        self.db = db
        self.model_class = model_class

    def get(self, id: str) -> ModelT | None:
        return self.db.get(self.model_class, id)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()  # get ID without commit
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
