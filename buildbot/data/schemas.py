import datetime
import uuid
from os import PathLike
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel

from buildbot.core.enums import JobStatus
from buildbot.settings import settings


class StorageBaseModel(BaseModel):
    """Base model for storage classes."""
    id: str = (
        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
    )

    def __eq__(self, other):
        if isinstance(other, StorageBaseModel):
            return self.id == other.id
        return False


class Task(StorageBaseModel):
    """Simple Task model."""

    script: str

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Task):
            return (
                self.__super__().__eq__(other)
                and self.script == other.script
            )
        return False


class Job(StorageBaseModel):
    """Simple Job model."""

    env_vars: Dict[str, str]
    task_id: str
    status: JobStatus = JobStatus.PENDING

    @property
    def output_path(self) -> Path:
        return settings.ARTIFACTS_PATH / self.id

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Job):
            return (
                self.__super__().__eq__(other)
                and self.env_vars == other.env_vars
                and self.task_id == other.task_id
            )
        return False
