from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import SingletonMeta
from buildbot.repository.job.artifact.schemas import JobArtifact


class JobArtifactRepository(ABC):
    """Interface for JobArtifact repository implementation classes."""

    @abstractmethod
    def add(self, job_artifact: JobArtifact) -> None:
        pass

    @abstractmethod
    def get_by_job_id(self, job_id: str) -> Optional[JobArtifact]:
        pass


class JobArtifactInMemoryRepository(JobArtifactRepository, metaclass=SingletonMeta):
    """In-memory JobArtifact Artifact Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, JobArtifact] = {}
        self._job_artifact_id_map: Dict[str, str] = {}
        self._logger = logger

    def add(self, job_artifact: JobArtifact) -> None:
        """Add a JobArtifact to the repository."""
        self._storage[job_artifact.id] = job_artifact

    def get_by_job_id(self, job_id: str) -> Optional[JobArtifact]:
        """Retrieve a JobArtifact by its Job ID."""
        id = self._job_artifact_id_map.get(job_id)
        return self._storage.get(id)


def get_job_artifact_repository() -> JobArtifactRepository:
    """Returns a JobArtifactRepository instance."""
    return JobArtifactInMemoryRepository()
