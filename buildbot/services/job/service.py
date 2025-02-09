from io import BytesIO
from pathlib import Path

import aiofiles
from fastapi import Depends
from loguru import logger

from buildbot.core.settings import settings
from buildbot.repository.job.repository import JobRepository, get_job_repository
from buildbot.repository.job.schemas import Job, JobStatus
from buildbot.services.job.schema import JobDTO
from buildbot.services.service_exceptions import (
    JobCreationException,
    JobFailedException,
    JobNotCompletedException,
    JobNotFoundException,
    JobOutputAccessDeniedException,
    TaskNotFoundException,
)
from buildbot.services.task.service import TaskService

BASE_OUTPUT_PATH: Path = settings.base_jobs_output_path.resolve()


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
        :raises JobCreationException: If the Job cannot be created
        :raises UnexpectedException: If an unexpected error occurs
        """
        try:
            _ = await self._task_svc.get(job_dto.task_id)
        except TaskNotFoundException as e:
            raise JobCreationException(
                "Could not create Job.", str(e)
            )
        job = Job(task_id=job_dto.task_id, env_vars=job_dto.env_vars)
        await self._job_repo.create(job)
        return job.id

    async def get_status(self, job_id: str) -> JobStatus:
        """
        Retrieve the status of a Job.

        :param job_id: The ID of the Job
        :return: The status of the Job
        :raises JobNotFoundException: If the Job is not found
        :raises UnexpectedException: If an unexpected error occurs while retrieving the Job
        """

        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundException(
                f"Could not retrieve status. Job(id={job_id}) not found"
            )

        return job.status

    async def get_output(self, job_id: str, file_path: str) -> BytesIO:
        """
        Retrieve a file from a Job's output.

        :param job_id: The ID of the Job
        :param file_path: The path to the file within the Job's output
        :return: The contents of the file
        :raises JobNotFoundException: If the Job does not exist or is not completed
        """
        job = await self._job_repo.get(job_id)
        if not job:
            raise JobNotFoundException(
                f"Job(id={job_id}) not found."
            )
        if job.status != JobStatus.SUCCEEDED:
            if job.status == JobStatus.FAILED:
                raise JobFailedException(
                    f"The Job(id={job_id}) has failed."
                )
            raise JobNotCompletedException(
                f"The Job(id={job_id}) has status '{job.status}'."
            )
        return await self._get_job_output(job_id, file_path)

    async def _get_job_output(self, job_id: str, path: Path) -> BytesIO:
        target = Path(path).resolve()

        if not target.is_relative_to(BASE_OUTPUT_PATH / job_id):
            raise JobOutputAccessDeniedException(
                "Target path is outside Job's base directory."
            )

        async with aiofiles.open(target, "rb") as f:
            return BytesIO(await f.read())


def get_job_service() -> JobService:
    return JobService()
