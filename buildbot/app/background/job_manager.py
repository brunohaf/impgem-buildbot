from __future__ import annotations

import asyncio
import tarfile
from datetime import datetime, timezone
from io import BytesIO, StringIO
from typing import Dict

import docker
import docker.errors
import loguru
from app.core.settings import settings
from app.repository.job.repository import JobRepository, get_job_repository
from app.repository.job.schemas import JobStatus
from app.services.storage import get_storage_service
from docker import DockerClient
from docker.errors import ImageNotFound
from docker.models.containers import Container
from docker.models.images import Image

_storage_service = get_storage_service()
_client: DockerClient = docker.from_env()
_job_repo: JobRepository = get_job_repository()
_logger: loguru.Logger = loguru.logger

JOB_ID_LABEL: str = "job_id"
DEQUEUED_COUNT_LABEL: str = "dequeued_count"
STDOUT: str = "stderr"
STDERR: str = "stdout"


def _format_docker_command(script_content: str) -> list[str]:
    return (
        '"cat <<EOF > run.sh'
        f"\n{script_content}"
        "\nEOF"
        "\nchmod +x run.sh"
        f"\ntimeout {settings.job_manager.script_timeout}"
        ' ./run.sh && rm run.sh"'
    )


def _get_container_logs(container: Container) -> Dict[str, StringIO]:
    logs = {
        STDOUT: StringIO(container.logs(stdout=True, stderr=False).decode("utf-8")),
        STDERR: StringIO(container.logs(stdout=False, stderr=True).decode("utf-8")),
    }
    return logs


def _get_image() -> Image:
    try:
        _logger.info("Checking for existing Docker image.")
        return _client.images.get(settings.job_manager.image_tag)
    except ImageNotFound:
        _logger.warning("Image not found. Building new image.")
        try:
            image, buildlogs = _client.images.build(
                tag=settings.job_manager.image_tag,
                path=str(settings.job_manager.dockerfile),
                buildargs={
                    "WORKDIR": str(settings.job_manager.workdir),
                },
            )
            for line in buildlogs:
                _logger.debug(f"Build log: {line}")
            return image
        except Exception as e:
            _logger.error(f"Error building image: {e}")
            raise


async def run_job(job_id: str, script: str, env_vars: dict) -> str:
    """Runs a Task in a Docker container asynchronously."""
    try:
        job_logger = _logger.bind(job_id=job_id)
        job_logger.info(f"Running job '{job_id}' in Docker container.")
        container = _client.containers.run(
            name=f"buildbotjob-{job_id}",
            image=_get_image(),
            command=_format_docker_command(script),
            hostname=job_id,
            environment=env_vars,
            network_mode="none",
            detach=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            stderr=True,
            stdout=True,
            labels={JOB_ID_LABEL: job_id},
        )
        await _job_repo.update_status(job_id, JobStatus.RUNNING)
        job_logger.info(f"Job '{job_id}' started successfully.")
        return job_id, container
    except Exception as e:
        job_logger.error(f"Error starting job '{job_id}': {e}")
        raise


async def manage_containers() -> None:
    """Pings for the containers status every X minutes."""
    _logger.info("Starting container status check cycle.")
    containers = _client.containers
    for container in containers.list(all=True):
        try:
            if not _should_process_container(container):
                continue
            job_id = container.labels.get(JOB_ID_LABEL)
            job_logger = _logger.bind(job_id=job_id)
            if container.status == "running":
                job_logger.info(f"Container '{container.name}' is still running.")
            else:
                _handle_container_termination(
                    job_id=job_id,
                    container=container,
                    job_logger=job_logger,
                )
        except Exception as e:
            job_logger.error(f"Error handling container termination: {e}")


def _should_process_container(container: Container) -> bool:
    if not container.labels.get(JOB_ID_LABEL):
        _logger.debug("Skipping container without job_id label.")
        return False
    return True


async def _handle_container_termination(
    job_id: str,
    container: Container,
    job_logger: loguru.Logger,
) -> None:
    """Handles the termination of a container, updating job status and saving outputs."""
    exit_code = container.attrs["State"]["ExitCode"]
    job_logger.info(
        f"Container '{container.name}' stopped with exit code {exit_code}.",
    )
    logs = _get_container_logs(container)
    if exit_code != 0:
        stderr = logs.get(STDERR)
        job_logger.error(
            f"Job '{job_id}' failed. Logs: {stderr.getvalue()}",
        )
        await _job_repo.update_status(job_id, JobStatus.FAILED)
    else:
        job_logger.info(f"Job '{job_id}' completed successfully.")
        await _job_repo.update_status(job_id, JobStatus.SUCCEEDED)

    tar_stream, _ = container.get_archive(str(settings.job_manager.workdir))
    await asyncio.gather(
        _save_artifact(tar_stream, job_id, job_logger),
        _save_logs(logs, job_id),
    )

    container.remove(force=True)


async def _save_artifact(
    container_tar_stream: BytesIO,
    job_id: str,
    job_logger: loguru.Logger,
) -> None:
    """Asynchronously gets a file from a Docker container and saves it locally."""
    try:
        job_logger.info(f"Saving outputs for job '{job_id}'.")

        artifact_path = f"{job_id}/artifact_{_get_targz_filename()}"

        path = await _storage_service.upload(artifact_path, container_tar_stream)

        job_logger.info(f"Job '{job_id}' outputs saved to {path}.")
    except Exception as e:
        job_logger.error(f"Error saving outputs for job '{job_id}': {e}")
        raise


# ? Webhook per job_id for realtime logs
async def _save_logs(logs: Dict[str, StringIO], job_id: str) -> None:
    try:
        logs_path = f"{job_id}/logs/{_get_targz_filename()}"

        tar_stream = BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
            for log_name, log_content in logs.items():
                log_data = log_content.getvalue()
                info = tarfile.TarInfo(name=log_name)
                info.size = len(log_data)
                tar.addfile(info, BytesIO(log_data))

            await _storage_service.upload(logs_path, tar_stream)

    except Exception as e:
        _logger.error(f"Error saving logs: {e}")


def _get_targz_filename() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.tar.gz"
