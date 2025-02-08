import datetime
import uuid

from pydantic import BaseModel


class RepositoryBaseModel(BaseModel):
    """Base model for repository classes."""

    id: str = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"

    def __eq__(self, other):
        if isinstance(other, RepositoryBaseModel):
            return self.id == other.id
        return False
