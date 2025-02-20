from __future__ import annotations

import tarfile
from io import BytesIO
from pathlib import Path

import loguru
from app.background.job_manager.manager_base import JobArtifactHandler
from app.background.job_manager.utils import JobOutput
from app.core.docker.utils import get_docker_client
from app.core.settings import settings
from app.services.storage import get_storage_service
from docker import DockerClient

_artifact_path_template: str = settings.job_manager_settings.artifact_path_template
_log_path_template: str = settings.job_manager_settings.log_path_template


class ContainerJobArtifactHandler(JobArtifactHandler):
    """Handles the management of Jobs running in Docker containers and their artifacts."""

    def __init__(self, docker_client: DockerClient = None) -> None:
        self._client = docker_client or get_docker_client()
        self._logger = loguru.logger.bind(artifact_handler=type(self))
        self._storage = get_storage_service()

    async def save_artifact(
        self,
        job_id: str,
        stream: BytesIO,
    ) -> Path:
        """Asynchronously gets a file from a Docker container and saves it locally."""
        try:
            job_logger = self._logger.bind(job_id=job_id)
            job_logger.info(f"Saving outputs for job '{job_id}'.")

            artifact_path = Path(
                _artifact_path_template.format(
                    job_id=job_id,
                ),
            )

            return await self._storage.upload(
                artifact_path,
                stream,
            )

        except Exception as e:
            job_logger.error(f"Error saving artifacts for job '{job_id}': {e}")
            raise

    # ? Docker-Py Outputs can be read in real time because
    # ? containers.log will return a bytes generator when stream==True
    # ? It would be possible to use it in a webhook endpoint per job_id
    # ? for realtime logs.
    async def handle_outputs(self, job_output: JobOutput) -> None:
        """Handles the Job logs."""
        try:
            logs_path = Path(
                _log_path_template.format(
                    job_id=job_output.job_id,
                ),
            )

            tar_stream = self._build_log_tar_stream(job_output)
            await self._storage.upload(logs_path, tar_stream)

        except Exception as e:
            self._logger.error(f"Error saving logs: {e}")
            raise

    def _build_log_tar_stream(self, job_output: JobOutput) -> BytesIO:
        """Builds a tar stream for the Job outputs."""
        tar_stream = BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
            for log_name, log_data in [
                ("stderr.log", job_output.stderr),
                ("stdout.log", job_output.stdout),
            ]:
                info = tarfile.TarInfo(name=log_name)
                log_data.seek(0)
                log_data_size = len(log_data.getvalue())
                info.size = log_data_size
                tar.addfile(info, log_data)

        tar_stream.seek(0)
        return tar_stream
