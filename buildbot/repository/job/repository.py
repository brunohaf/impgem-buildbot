import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import AbstractSingletonMeta
from buildbot.repository.job.schemas import Job


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


class JobInMemoryRepository(JobRepository, metaclass=AbstractSingletonMeta):
    """In-memory Job Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, Job] = {}
        self._logger = logger
        self._lock = asyncio.Lock()

    async def create(self, job: Job) -> None:
        self._logger.info(f"Creating Job(id={job.id})")
        async with self._lock:
            self._storage[job.id] = job
        self._logger.info(f"Job(id={job.id}) successfully created.")
        return

    async def get(self, id: str) -> Optional[Job]:
        """Retrieve a Job by its ID."""
        self._logger.info(f"Getting Job(id={id})")
        job = self._storage.get(id)
        await asyncio.sleep(0.1)
        if job is None:
            self._logger.info(f"Cannot retrieve Job(id={id}). Not found")
        self._logger.info(f"Successfully retrieved Job(id={id})")
        return job

    async def update(self, new_job: Job) -> None:  # ! make it merge
        """Updates existing Job."""
        self._logger.info(f"Updating Job(id={new_job.id})")
        async with self._lock:
            if self._storage.get(new_job.id) is None:
                self._logger.info(f"Failed to update Job(id={id}). Not found")
            self._storage[new_job.id] = new_job
        self._logger.info(f"Successfully updated Job(id={new_job.id})")
        return


def get_job_repository() -> JobRepository:
    """Returns the singleton JobRepository instance."""
    return JobInMemoryRepository()
