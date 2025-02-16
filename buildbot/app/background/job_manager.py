"""JobManager is a class that runs Jobs in Docker containers."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import aiofiles
import loguru
from app.core.settings import settings
from docker import DockerClient
from docker import from_env as get_docker_client_from_env
from docker.models.containers import Container

from buildbot.app.background.broker import broker
from buildbot.app.repository.job.repository import JobRepository, get_job_repository
from buildbot.app.repository.job.schemas import JobStatus

BASE_WORKDIR: Path = settings.buildbot_job.base_workdir.resolve()
STORAGE_DIR: Path = Path.cwd() / "buildbot" / "app" / "background" / "outputs"
DOCKERFILE: Path = Path.cwd() / "buildbot" / "app" / "background"
RUNNER_TAG: str = "jobrunner"
RUNNER_USER: str = "jobrunner"
RUNNER_GROUP: str = "jobrunner"
PERSISTENT_VOLUME: str = "buildbot_data"
OUTPUT_DIR = BASE_WORKDIR / "outputs"
TIME_TO_CHECK_CONTAINER_STATUS: timedelta = timedelta(minutes=2)


_client: DockerClient = get_docker_client_from_env()
_job_repo: JobRepository = get_job_repository()
_logger: loguru.Logger = loguru.logger


@broker.task
async def run_job_in_container(job_id: str, script: str, env_vars: dict) -> str:
    """Runs a Task in a Docker container asynchronously."""
    workdir = BASE_WORKDIR / job_id
    script = f"#!/bin/sh\n{script}\nexit 0"
    script_file = workdir / "script.sh"
    command = [
        f'echo -e "{script}" > {script_file} && chmod +x script.sh && ./script.sh',
    ]

    try:
        image, _ = _client.images.build(
            tag=f"{RUNNER_TAG}:job-{job_id}",
            path=str(DOCKERFILE),
            buildargs={
                "RUNNER_USER": RUNNER_USER,
                "RUNNER_GROUP": RUNNER_GROUP,
                "WORKDIR": str(workdir),
            },
            labels={"job_id": job_id},
        )
        container = _client.containers.run(
            image=image,
            command=command,
            hostname=f"task-runner-{job_id}",
            environment=env_vars,
            network_mode="none",
            detach=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges"],
            stderr=True,
            stdout=True,
        )

        for log_line in container.logs(stream=True, follow=True):
            print(log_line.decode("utf-8"), end="")

        await _save_outputs(container, job_id)
        return job_id, container
    except Exception as e:
        raise e
    finally:
        _client.images.remove(image.id, force=True)


@broker.task(schedule=[{"cron": "*/5 * * * *"}])
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


async def _save_outputs(
    container: Container,
    job_id: str,
) -> None:
    """Asynchronously gets a file from a Docker container and saves it locally."""

    stream, _ = container.get_archive(str(BASE_WORKDIR / job_id))

    Path(STORAGE_DIR).parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(STORAGE_DIR / f"{job_id}.tar.gz", "wb") as f:
        for chunk in stream:
            await f.write(chunk)
