from io import BytesIO
from pathlib import Path

import aiofiles
from app.core.exceptions import (
    JobCreationError,
    JobNotCompletedError,
    JobNotFoundError,
    JobOutputAccessDeniedError,
    TaskNotFoundError,
)
from app.core.settings import settings
from app.repository.job.repository import JobRepository, get_job_repository
from app.repository.job.schemas import Job, JobStatus
from app.services.job.schema import JobDTO
from app.services.task.service import TaskQueryService, get_task_service
from fastapi import Depends
from loguru import logger

BASE_OUTPUT_PATH: Path = settings.buildbot_job.base_output_path.resolve()


class JobService:
    """Service for Job operations."""

    def __init__(
        self,
        job_repo: JobRepository = Depends(get_job_repository),
        task_svc: TaskQueryService = Depends(get_task_service),
    ) -> None:
        self._logger = logger
        self._job_repo = job_repo
        self._task_svc = task_svc

    async def _check_task_exists(self, task_id: str) -> None:
        try:
            _ = await self._task_svc.get(task_id)
        except TaskNotFoundError as e:
            raise JobCreationError(task_id) from e

    async def create(self, job_dto: JobDTO) -> str:
        """
        Create a Job.

        :param job_dto: The JobDTO
        :return: The ID of the created Job
        :raises JobCreationError: If the Job cannot be created
        :raises UnexpectedException: If an unexpected error occurs
        """
        await self._check_task_exists(job_dto.task_id)
        try:
            job = Job(task_id=job_dto.task_id, env_vars=job_dto.env_vars)
            await self._job_repo.create(job)
            await self._job_repo.associate_job_with_task(job.id, job.task_id)
            # await job_runner_task.send(job, task)
            return job.id
        except Exception as e:
            raise JobCreationError() from e

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
        if not target.is_relative_to(BASE_OUTPUT_PATH / job_id):
            raise JobOutputAccessDeniedError(job_id, path)
        async with aiofiles.open(target, "rb") as f:
            return BytesIO(await f.read())


def get_job_service() -> JobService:
    """Get a JobService instance."""
    return JobService()
