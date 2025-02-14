import uuid
from datetime import datetime, timezone

from pydantic import BaseModel


class RepositoryBaseModel(BaseModel):
    """Base model for repository classes."""

    id: str = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex}"

    class Config:
        ignore_extra = True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RepositoryBaseModel):
            return self.id == other.id
        return False
