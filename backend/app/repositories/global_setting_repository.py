"""GlobalSetting repository - e.g. retention_days default."""

from sqlalchemy.orm import Session

from app.models.global_setting import GlobalSetting
from app.repositories.base import BaseRepository


class GlobalSettingRepository(BaseRepository[GlobalSetting]):
    def __init__(self, db: Session):
        super().__init__(db, GlobalSetting)

    def get_value(self, key: str) -> str | None:
        row = self.db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
        return row.value if row else None

    def set_value(self, key: str, value: str) -> GlobalSetting:
        row = self.db.query(GlobalSetting).filter(GlobalSetting.key == key).first()
        if row:
            row.value = value
            self.db.flush()
            return row
        row = GlobalSetting(key=key, value=value)
        self.db.add(row)
        self.db.flush()
        return row

    def get_retention_days(self) -> int | None:
        """Return retention_days from DB if set; else None (use config default)."""
        v = self.get_value("retention_days")
        if v is None:
            return None
        try:
            return int(v)
        except ValueError:
            return None
