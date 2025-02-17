"""JobManager is a class that runs Jobs in Docker containers."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path

import aiofiles
import loguru
from app.core.settings import settings
from app.repository.job.repository import JobRepository, get_job_repository
from app.repository.job.schemas import JobStatus
from docker import DockerClient
from docker import from_env as get_docker_client_from_env
from docker.errors import ImageNotFound
from docker.models.containers import Container
from docker.models.images import Image

WORKDIR: Path = settings.buildbot_job.base_workdir.resolve()
STORAGE_DIR: Path = Path.cwd() / "buildbot" / "data"
IMAGE_TAG: str = "buildbot-job-runner:latest"
DOCKERFILE: Path = Path.cwd() / "buildbot" / "app" / "background"
TIME_TO_CHECK_CONTAINER_STATUS: timedelta = timedelta(minutes=2)
SCRIPT_TIMEOUT: str = "5m"

_client: DockerClient = get_docker_client_from_env()
_job_repo: JobRepository = get_job_repository()
_logger: loguru.Logger = loguru.logger


def _get_image() -> Image:
    try:
        return _client.images.get(IMAGE_TAG)
    except ImageNotFound:
        image, buildlogs = _client.images.build(
            tag=IMAGE_TAG,
            path=str(DOCKERFILE),
            buildargs={
                "WORKDIR": str(WORKDIR),
            },
        )

        for line in buildlogs:
            _logger.info(line)
        return image


async def run_job_in_container(job_id: str, script: str, env_vars: dict) -> str:
    """Runs a Task in a Docker container asynchronously."""
    try:
        command = (
            '"cat <<EOF > run.sh'
            f"\n{script}"
            "\nEOF"
            "\nchmod +x run.sh"
            f"\ntimeout {SCRIPT_TIMEOUT}"
            ' ./run.sh"'
        )
        image = _get_image()
        container = _client.containers.run(
            image=image,
            command=command,
            hostname=job_id,
            environment=env_vars,
            network_mode="none",
            detach=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            stderr=True,
            stdout=True,
            labels={"job_id": job_id},
        )
        await asyncio.sleep(4)
        await _save_outputs(container, job_id)
        return job_id, container
    except Exception as e:
        raise e


async def check_container_status() -> None:
    """Pings for the containers status every X minutes."""
    containers = _client.containers
    for container in containers.list(all=True):
        job_id = container.attrs["Config"]["Labels"]["job_id"]
        container_name = f"task-runner-{job_id}"
        if container.status == "running":
            _logger.info(f"Container {container_name} is still running.")
        else:
            exit_code = container.attrs["State"]["ExitCode"]
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            _job_repo.update_status(job_id, JobStatus.FAILED)
            if exit_code != 0:
                _logger.error(
                    f"Container {container_name} failed with exit code {exit_code}."
                    f"Logs: {logs}",
                )
            else:
                _logger.info(
                    f"Container {container_name} completed successfully.",
                )
                await _save_outputs(container, job_id)
            _client.containers.prune()
            _client.images.remove(container.image.id, force=True)


async def _save_outputs(
    container: Container,
    job_id: str,
) -> None:
    """Asynchronously gets a file from a Docker container and saves it locally."""

    stream, _ = container.get_archive(str(WORKDIR))

    Path(STORAGE_DIR).parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(STORAGE_DIR / f"{job_id}.tar.gz", "wb") as f:
        for chunk in stream:
            await f.write(chunk)
