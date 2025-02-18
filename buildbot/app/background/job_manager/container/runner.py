from __future__ import annotations

import loguru
from app.background.job_manager.container.utils import Labels, get_docker_client
from app.background.job_manager.manager_base import JobRunner
from app.core.settings import settings
from docker import DockerClient
from docker.errors import ImageNotFound
from docker.models.images import Image

_container_settings = settings.job_manager.container


class ContainerRunner(JobRunner):
    """Runs Jobs in Docker containers asynchronously."""

    def __init__(self, docker_client: DockerClient = None) -> None:
        self._client = docker_client or get_docker_client()
        self._logger = loguru.logger.bind(job_runner=type(self))

    async def run(self, job_id: str, script: str, env_vars: dict) -> str:
        """Runs a Task in a Docker container asynchronously."""
        try:
            job_logger = self._logger.bind(job_id=job_id)
            job_logger.info(f"Running job '{job_id}' in Docker container.")
            _ = self._client.containers.run(
                name=f"buildbotjob-{job_id}",
                image=self._get_image(),
                command=self._format_docker_command(script),
                hostname=job_id,
                environment=env_vars,
                labels={Labels.JOB_ID: job_id},
                **_container_settings.config,
            )
            return job_id
        except Exception as e:
            job_logger.error(f"Error starting job '{job_id}': {e}")
            raise

    def _get_image(self) -> Image:
        try:
            self._logger.info("Checking for existing Docker image.")
            return self._client.images.get(_container_settings.tag)
        except ImageNotFound:
            self._logger.warning("Image not found. Building new image.")
            try:
                image, build_logs = self._client.images.build(
                    buildargs={"WORKDIR": str(settings.job_manager.workdir)},
                    **_container_settings.image_config,
                )
                for line in build_logs:
                    self._logger.debug(f"Build log: {line}")
                return image
            except Exception as e:
                self._logger.error(f"Error building image: {e}")
                raise

    def _format_docker_command(self, script: str) -> list[str]:
        return _container_settings.command_template.format(
            script=script,
            timeout=settings.job_manager.job_ttl,
        )
