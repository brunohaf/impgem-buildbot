from abc import ABC, abstractmethod
from io import BytesIO
from typing import Dict

from app.background.job_manager.utils import JobOutput
from app.repository.job.repository import JobRepository
from app.services.storage import StorageService


class JobArtifactHandler(ABC):
    """Job Handler interface."""

    _storage: StorageService

    @abstractmethod
    async def save_artifact(self, job_id: str, stream: BytesIO) -> None:
        """Handles the Job Artifact."""

    @abstractmethod
    async def handle_outputs(self, job_id: str, job_output: JobOutput) -> None:
        """Handles the Job outputs."""


class JobRunner(ABC):
    """Job Runner interface."""

    @abstractmethod
    async def run(self, job_id: str, script: str, env_vars: Dict[str, str]) -> None:
        """Runs a Job."""


class JobManager(ABC):
    """Job Manager interface."""

    _handler: JobArtifactHandler
    _runner: JobRunner
    _job_repo: JobRepository

    @abstractmethod
    async def process(self, job_id: str, script: str, env_vars: Dict[str, str]) -> None:
        """Processes a Job."""
