import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

from fastapi import Depends
from loguru import logger
from virtualenv import create

from buildbot.core.settings import settings
from buildbot.repository.job.base_repository import JobRepository
from buildbot.repository.job.schemas import Job, JobStatus

BASE_OUTPUT_PATH: Path = settings.base_jobs_output_path.resolve()


class RunnerJob:
    def __init__(self, script: str, env_vars: Dict[str, str], job_id: str):
        self.script = script
        self.env_vars = env_vars
        self.job_id = job_id


def setup_virtualenv(env_vars: Dict[str, str]):
    temp_venv_dir = Path(tempfile.mkdtemp()) / "venv"
    create(str(temp_venv_dir))
    env = os.environ.copy()
    env.update(env_vars)
    env["PATH"] = str(temp_venv_dir / "bin") + ":" + env.get("PATH", "")
    yield env
    try:
        temp_venv_dir.rmdir()
    except Exception as e:
        logger.error(f"Failed to clean up virtual environment: {e}")


async def stream_output(stream, level):
    """Streams the output of a given stream to Loguru."""
    while True:
        line = await asyncio.to_thread(stream.readline)
        if not line:
            break
        logger.log(level, line.decode().strip())


async def run(runner_job: RunnerJob, job_repository: JobRepository = Depends()) -> str:
    """
    Run a bash script in an isolated environment, log outputs in real-time.
    - Create a new virtual environment for isolation.
    - Run the script in a subprocess.
    - Stream the script’s output to Loguru in real-time.
    - Clean up the environment once the task is completed.
    """
    try:
        job_path = BASE_OUTPUT_PATH / runner_job.job_id
        log_file = job_path/"job_log.log"
        logger.bind(job_id=runner_job.job_id).add(log_file, level="INFO", rotation="10 MB", compression="zip")

        await job_repository.update(Job(runner_job.job_id, JobStatus.RUNNING))

        with setup_virtualenv(runner_job.env_vars) as env:
            process = subprocess.Popen(
                ["bash", "-c", runner_job.script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(job_path),
            )

            await asyncio.gather(
                stream_output(process.stdout, "INFO"),
                stream_output(process.stderr, "ERROR"),
            )
            # ! if stderr?? setup as error
            await job_repository.update(
                Job(runner_job.job_id, JobStatus.FAILED)
            )

            await asyncio.to_thread(process.wait)
        await job_repository.update(Job(runner_job.job_id, JobStatus.SUCCEEDED))
        return
    except Exception as e:
        logger.error(f"Failed to run bash script: {e}")
