from enum import StrEnum
from typing import Dict

from buildbot.repository.schemas import RepositoryBaseModel


class JobStatus(StrEnum):
    """
    Enum for job status.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Job(RepositoryBaseModel):
    """Simple Job model."""

    env_vars: Dict[str, str]
    task_id: str
    status: JobStatus = JobStatus.PENDING

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Job):
            return (
                self.__super__().__eq__(other)
                and self.env_vars == other.env_vars
                and self.task_id == other.task_id
                and self.status == other.status
            )
        return False
