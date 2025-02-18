import asyncio
from io import StringIO
from typing import Dict

import loguru
from app.background.job.container.handler import ContainerArtifactHandler
from app.background.job.container.runner import ContainerRunner
from app.background.job.container.utils import ContainerStatus as Status
from app.background.job.container.utils import Labels
from app.background.job.manager import JobManager
from app.background.job.utils import JobOutput, OutputType
from app.core import settings
from app.repository.job.repository import get_job_repository
from app.repository.job.schemas import JobStatus
from docker.models.containers import Container
from loguru import logger


class ContainerManager(JobManager):
    """Container Job Manager."""

    def __init__(self) -> None:
        self._logger = logger.bind(job_manager=type(self))
        self._handler = ContainerArtifactHandler()
        self._runner = ContainerRunner()
        self._job_repo = get_job_repository()

    async def process(self, job_id: str, script: str, env_vars: Dict[str, str]) -> None:
        """Processes the Jobs."""
        self._logger.info(f"Processing job '{job_id}'.")
        await self._runner.run(job_id, script, env_vars)
        self._logger.info(f"Job '{job_id}' processed successfully.")

    async def manage_jobs(self) -> None:
        """Handles the termination of a container, updating job status and saving outputs."""
        self._logger.info("Starting container status check cycle.")
        containers = self._client.containers
        for container in containers.list(all=True):
            try:
                job_id = container.labels.get(Labels.JOB_ID)
                job_logger = self._logger.bind(job_id=job_id)
                if not job_id:
                    self._logger.debug("Skipping container without job_id label.")
                    continue
                if container.status == Status.RUNNING:
                    job_logger.info(f"Container '{container.name}' is still running.")
                else:
                    self._handle_container_termination(
                        job_id=job_id,
                        job_logger=job_logger,
                        container=container,
                    )
            except Exception as e:
                job_logger.error(f"Error handling container termination: {e}")

    async def _handle_container_termination(
        self,
        job_id: str,
        container: Container,
        job_logger: loguru.Logger,
    ) -> None:
        """Handles the termination of a container, updating job status and saving outputs."""
        exit_code = container.attrs["State"]["ExitCode"]
        job_logger.info(
            f"Container '{container.name}' stopped with exit code {exit_code}.",
        )
        logs = self._get_container_logs(container)
        if exit_code != 0:
            self._handle_errors(logs, job_id, job_logger)
        else:
            job_logger.info(f"Job '{job_id}' completed successfully.")
            await self._job_repo.update_status(job_id, JobStatus.SUCCEEDED)

        tar_stream, _ = container.get_archive(str(settings.job_manager.workdir))
        await asyncio.gather(
            self._handler.save_artifact(job_id, tar_stream),
            self._handler.handle_outputs(JobOutput(job_id, **logs)),
        )

        container.remove(force=True)

    def _get_container_logs(self, container: Container) -> Dict[str, StringIO]:
        return {
            OutputType.STDOUT: StringIO(container.logs(stdout=True, stderr=False)),
            OutputType.STDERR: StringIO(container.logs(stdout=False, stderr=True)),
        }

    async def _handle_errors(
        self,
        stderr_stream: StringIO,
        job_id: str,
        job_logger: loguru.Logger,
    ) -> None:
        stderr = stderr_stream.getvalue().decode("utf-8")
        job_logger.error(f"Job '{job_id}' failed. Logs: {stderr}")
        await self._job_repo.update_status(job_id, JobStatus.FAILED)
