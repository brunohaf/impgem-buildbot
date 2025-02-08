import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import SingletonMeta
from buildbot.repository.job.schemas import Job
from buildbot.repository.repository_exceptions import JobNotFoundException


class JobRepository(ABC):
    """Interface for Job repository implementation classes."""

    @abstractmethod
    async def create(self, job: Job) -> None:
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Job]:
        pass

    @abstractmethod
    async def update(self, new_job: Job) -> None:
        pass


class JobInMemoryRepository(JobRepository, metaclass=SingletonMeta):
    """In-memory Job Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, Job] = {}
        self._logger = logger

    async def create(self, job: Job) -> None:
        """Add a Job to the repository."""
        self._logger.info(f"Creating Job(id={job.id})")
        self._storage[job.id] = job
        self._logger.info(f"Job(id={job.id}) successfully created.")

    async def get(self, id: str) -> Optional[Job]:
        """Retrieve a Job by its ID."""
        self._logger.info(f"Getting Job(id={id})")
        job = self._storage.get(id)
        if job is None:
            self._logger.info(f"Cannot retrieve Job(id={id}). Not found")
        return job

    async def update(self, new_job: Job) -> None:
        """Update an existing Job."""
        self._logger.info(f"Updating Job(id={new_job.id})")
        if new_job.id not in self._storage:
            self._logger.info(
                f"Failed to update Job(id={new_job.id}). Not found"
            )
            return
        self._storage[new_job.id] = new_job
        self._logger.info(f"Successfully updated Job(id={new_job.id})")
        return


def get_job_repository() -> JobRepository:
    """Returns the singleton JobRepository instance."""
    return JobInMemoryRepository()
