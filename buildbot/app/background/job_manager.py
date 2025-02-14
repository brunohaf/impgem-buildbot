from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Dict

import loguru
import taskiq
from app.core.settings import settings
from docker import DockerClient
from docker import from_env as get_docker_client_from_env

BASE_WORKDIR: Path = settings.buildbot_job.base_workdir.resolve()

DOCKER_IMAGE: str = "alpine:latest"
RUNNER_USER: str = "jobrunner"
RUNNER_GROUP: str = "jobrunner"
PERSISTENT_VOLUME: str = "job_outputs"
OUTPUT_DIR = BASE_WORKDIR / "outputs"

client: DockerClient = get_docker_client_from_env()
_logger: loguru.Logger = loguru.logger


class JobRun:
    """A Job to be run by the JobManager."""

    def __init__(self, script: str, env_vars: Dict[str, str], job_id: str) -> None:
        self.script = script
        self.env_vars = env_vars
        self.job_id = job_id


class JobManager:
    def __init__(self, client: DockerClient):
        self.client = client
        self.logger = _logger

    @taskiq.task
    def run_job_in_container(self, job_id: str, script: str, env_vars: dict) -> str:
        """Runs a Task in a Docker container asynchronously."""
        script = f"#!/bin/sh\n{script}\nexit 0"
        workdir = {BASE_WORKDIR} / {job_id}
        script_file = workdir / "script.sh"
        command = (
            f"chroot {workdir} /bin/bash -c'"
            f"mkdir -p /tmp/workdir{job_id} && chown -r {RUNNER_USER}:{RUNNER_GROUP}"
            f"mkdir -p {OUTPUT_DIR} &&  && chown -rw {RUNNER_USER}:{RUNNER_GROUP}"
            f"echo '{script}' > {script_file} && chmod +x {script_file}"
            f"{script} > /log/stdout.log 2> /log/stderr.log; "
        )

        container = self.client.containers.run(
            DOCKER_IMAGE,
            name=f"task-runner-{job_id}",
            command=command,
            environment=env_vars,
            volumes={PERSISTENT_VOLUME: {"bind": OUTPUT_DIR, "mode": "rw"}},
            network_mode="none",
            working_dir=workdir,
            detach=True,
            auto_remove=True,
            cap_drop=["ALL"],
            user=RUNNER_USER,
            security_opt=["no-new-privileges"],
            readonly_rootfs=True,
        )

        return job_id, container

    @taskiq.task
    async def check_container_status(self, job_id: str) -> None:
        """Pings for the container's status every X minutes."""
        container_name = f"task-runner-{job_id}"
        container = await self.client.containers.get(container_name)

        if container.status == "running":
            self.logger.info(f"Container {container_name} is still running.")
        else:
            exit_code = container.attrs["State"]["ExitCode"]
            logs = await container.logs(stdout=True, stderr=True).decode("utf-8")

            if exit_code == 0:
                self.logger.info(f"Container {container_name} completed successfully.")
            else:
                self.logger.error(
                    f"Container {container_name} failed with exit code {exit_code}. Logs: {logs}",
                )

        # Reschedule the task to ping again in 5 minutes
        self.check_container_status.schedule_in(
            timedelta(minutes=5),
            job_id=job_id,
        )


def get_job_manager() -> JobManager:
    return JobManager(client=client)
