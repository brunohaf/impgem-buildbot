from __future__ import annotations

import docker
import loguru
from app.background.job.container.utils import Constants
from app.background.job.manager import JobRunner
from docker.errors import ImageNotFound
from docker.models.images import Image

from buildbot.app.core.settings import settings


class ContainerRunner(JobRunner):
    """Runs Jobs in Docker containers asynchronously."""

    def __init__(self) -> None:
        self._client = docker.from_env()
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
                network_mode="none",
                detach=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                stderr=True,
                stdout=True,
                labels={Constants.Labels.JOB_ID: job_id},
            )
            return job_id
        except Exception as e:
            job_logger.error(f"Error starting job '{job_id}': {e}")
            raise

    def _get_image(self) -> Image:
        try:
            self._logger.info("Checking for existing Docker image.")
            return self._client.images.get(settings.job_manager.image_tag)
        except ImageNotFound:
            self._logger.warning("Image not found. Building new image.")
            try:
                image, buildlogs = self._client.images.build(
                    tag=settings.job_manager.image_tag,
                    path=str(settings.job_manager.dockerfile),
                    buildargs={
                        "WORKDIR": str(settings.job_manager.workdir),
                    },
                )
                for line in buildlogs:
                    self._logger.debug(f"Build log: {line}")
                return image
            except Exception as e:
                self._logger.error(f"Error building image: {e}")
                raise

    def _format_docker_command(self, script_content: str) -> list[str]:
        return (
            '"cat <<EOF > run.sh'
            f"\n{script_content}"
            "\nEOF"
            "\nchmod +x run.sh"
            f"\ntimeout {settings.job_manager.timeout}"
            ' ./run.sh && rm run.sh"'
        )
