from io import BytesIO
from pathlib import Path

import aiofiles
from app.core.exceptions import (
    JobCreationError,
    JobNotCompletedError,
    JobNotFoundError,
    JobOutputAccessDeniedError,
    JobSchedulingError,
    TaskNotFoundError,
)
from app.core.settings import settings
from app.repository.job.repository import JobRepository, get_job_repository
from app.repository.job.schemas import Job, JobStatus
from app.services.job.schema import JobDTO
from fastapi import Depends
from loguru import logger

from buildbot.app.background import broker
from buildbot.app.repository.task.schemas import Task
from buildbot.app.services.task.service import TaskService

base_workdir: Path = settings.buildbot_job.base_workdir.resolve()


class JobService:
    """Service for Job operations."""

    def __init__(
        self,
        job_repo: JobRepository = Depends(get_job_repository),
        task_svc: TaskService = Depends(),
    ) -> None:
        self._logger = logger
        self._job_repo = job_repo
        self._task_svc = task_svc

    async def create(self, job_dto: JobDTO) -> str:
        """
        Create a Job.

        :param job_dto: The JobDTO
        :return: The ID of the created Job
        :raises JobCreationError: If the Job cannot be created
        :raises UnexpectedException: If an unexpected error occurs
        """
        try:
            task = await self._task_svc.get(job_dto.task_id)
            job = Job(task_id=job_dto.task_id, env_vars=job_dto.env_vars)
            job_id = await self._job_repo.create(job)
            await self._schedule_job(job, task)
            return job_id
        except TaskNotFoundError as e:
            raise JobCreationError(job_dto.task_id) from e

    async def get_status(self, job_id: str) -> JobStatus:
        """
        Retrieve the status of a Job.

        :param job_id: The ID of the Job
        :return: The status of the Job
        :raises JobNotFoundError: If the Job is not found.
        """
        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        return job.status

    async def get_output(self, job_id: str, file_path: str) -> BytesIO:
        """
        Retrieve a file from a Job's output.

        :param job_id: The ID of the Job
        :param file_path: The path to the file within the Job's output
        :return: The contents of the file
        :raises JobNotFoundError: If the Job was not found.
        :raises JobNotCompletedError: If the Job has failed.
        :raises JobNotCompletedError: If the Job is not completed.
        """
        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        if job.status != JobStatus.SUCCEEDED:
            if job.status == JobStatus.FAILED:
                raise JobNotCompletedError(job_id)
            raise JobNotCompletedError(job_id, job.status)
        return await self._get_job_output(job_id, file_path)

    async def _get_job_output(self, job_id: str, path: Path) -> BytesIO:
        target = Path(path).resolve()
        if not target.is_relative_to(base_workdir / job_id):
            raise JobOutputAccessDeniedError(job_id, path)
        async with aiofiles.open(target, "rb") as f:
            return BytesIO(await f.read())

    async def _schedule_job(self, job: Job, task: Task) -> None:
        try:
            await broker.run_job.kiq(
                job.id,
                task.script,
                job.env_vars,
            )
        except Exception as e:
            raise JobSchedulingError from e


async def get_job_service() -> JobService:
    """Get the JobService."""
    return JobService()
