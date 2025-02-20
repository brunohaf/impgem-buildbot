from __future__ import annotations

import asyncio
from io import BytesIO

import loguru
from app.background.job_manager.container.handler import ContainerJobArtifactHandler
from app.background.job_manager.manager_base import JobManager
from app.background.job_manager.utils import JobOutput
from app.core.docker.utils import ContainerStatus as Status
from app.core.docker.utils import Labels, get_docker_client
from app.core.settings import ContainerJobManagerSettings, settings
from app.repository.job.repository import get_job_repository
from app.repository.job.schemas import JobStatus
from docker.models.containers import Container
from loguru import logger

_container_settings: ContainerJobManagerSettings = settings.job_manager_settings


# ? Fallback background task to collect pending jobs
class ContainerJobManager(JobManager):
    """Container Job Manager."""

    def __init__(self) -> None:
        self._logger = logger.bind(job_manager=type(self))
        self._client = get_docker_client()
        self._handler = ContainerJobArtifactHandler(self._client)
        self._job_repo = get_job_repository()

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
                    await self._handle_container_termination(
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
        try:
            exit_code = container.attrs["State"]["ExitCode"]
            job_logger.info(
                f"Container '{container.name}' stopped with exit code {exit_code}.",
            )
            logs = self._get_container_logs(container, job_id)
            if exit_code != 0:
                await self._handle_errors(logs.stderr, job_id, job_logger)
            else:
                job_logger.info(f"Job '{job_id}' completed successfully.")
                await self._job_repo.update_status(job_id, JobStatus.SUCCEEDED)

            tar_stream, _ = container.get_archive(
                str(_container_settings.workdir),
            )
            await asyncio.gather(
                self._handler.save_artifact(job_id, tar_stream),
                self._handler.handle_outputs(logs),
            )

            container.remove(force=True)
        except Exception as e:
            job_logger.error(f"Error handling container termination: {e}")
            raise

    def _get_container_logs(self, container: Container, job_id: str) -> JobOutput:
        return JobOutput(
            job_id=job_id,
            stderr=container.logs(stdout=False, stderr=True),
            stdout=container.logs(stdout=True, stderr=False),
        )

    async def _handle_errors(
        self,
        stderr: BytesIO,
        job_id: str,
        job_logger: loguru.Logger,
    ) -> None:
        stderr.seek(0)
        stderr_str = stderr.getvalue().decode("utf-8", errors="replace")
        job_logger.error(f"Job '{job_id}' failed. Logs: {stderr_str}")
        await self._job_repo.update_status(job_id, JobStatus.FAILED)


def get_container_manager() -> ContainerJobManager:
    """Returns a ContainerJobManager instance."""
    return ContainerJobManager()
