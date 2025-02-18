from __future__ import annotations

import tarfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict

import loguru
from app.background.job.container.utils import get_docker_client
from app.background.job.manager import JobArtifactHandler
from app.background.job.utils import get_tar_filename
from app.core.settings import settings
from app.services.storage import get_storage_service


class ContainerArtifactHandler(JobArtifactHandler):
    """Handles the management of Jobs running in Docker containers and their artifacts."""

    def __init__(self) -> None:
        self._client = get_docker_client()
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
                settings.job_manager.logs_path_template.format(
                    job_id=job_id,
                    filename=get_tar_filename(),
                ),
            )

            return await self._storage.upload(
                artifact_path,
                stream,
            )

        except Exception as e:
            job_logger.error(f"Error saving artifacts for job '{job_id}': {e}")
            raise

    # ? Webhook per job_id for realtime logs
    async def handle_logs(self, logs: Dict[str, StringIO], job_id: str) -> None:
        """Handles the Job logs."""
        try:
            logs_path = Path(
                settings.job_manager.logs_path_template.format(
                    job_id=job_id,
                    filename=get_tar_filename(),
                ),
            )

            tar_stream = BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
                for log_name, log_content in logs.items():
                    log_data = log_content.getvalue()
                    info = tarfile.TarInfo(name=log_name)
                    info.size = len(log_data)
                    tar.addfile(info, BytesIO(log_data))

                await self._storage.upload(logs_path, tar_stream)

        except Exception as e:
            self._logger.error(f"Error saving logs: {e}")
