from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import SingletonMeta
from buildbot.repository.job.schemas import Job


class JobRepository(ABC):
    """Interface for Job repository implementation classes."""

    @abstractmethod
    def add(self, job: Job) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[Job]:
        pass

    @abstractmethod
    def update(self, new_job: Job) -> Optional[Job]:
        pass


class JobInMemoryRepository(JobRepository, metaclass=SingletonMeta):
    """In-memory Job Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, Job] = {}
        self._logger = logger

    def add(self, job: Job) -> None:
        """Add a Job to the repository."""
        self._storage[job.id] = job

    def get(self, id: str) -> Optional[Job]:
        """Retrieve a Job by its ID."""
        return self._storage.get(id)

    def update(self, new_job: Job) -> Optional[Job]:
        """Updates existing Job."""

        if self._storage.get(new_job.id) is None:
            self._logger.info(
                f"Failed to update Job(id={new_job.id}) because it doesn't exist",
            )
            return None

        self._storage[new_job.id] = new_job
        self._logger.info(f"Successfully updated Job(id={new_job.id})")

        return new_job


def get_job_repository() -> JobRepository:
    """Returns a JobRepository instance."""
    return JobInMemoryRepository()
