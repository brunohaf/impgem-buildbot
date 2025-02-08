from pathlib import Path
from typing import Optional

from fastapi import Depends
from loguru import logger

from buildbot.api.job.schema import CreateJobRequest
from buildbot.core.utils import SingletonMeta
from buildbot.repository.job.artifact.repository import (
    JobArtifactRepository,
    get_job_artifact_repository,
)
from buildbot.repository.job.artifact.schemas import JobArtifact
from buildbot.repository.job.repository import JobRepository, get_job_repository
from buildbot.repository.job.schemas import Job, JobStatus
from buildbot.services import job_utils
from buildbot.services.service_exceptions import (
    JobArtifactNotFoundException,
    JobCreationException,
    JobNotFoundException,
    UnexpectedException,
)


class JobService(metaclass=SingletonMeta):
    """Service for Job operations."""

    def __init__(
        self,
        job_repo: JobRepository = Depends(get_job_repository),
        artifact_repo: JobArtifactRepository = Depends(get_job_artifact_repository),
    ) -> None:
        self._logger = logger
        self._job_repo = job_repo
        self._artifact_repo = artifact_repo

    def create(self, job_request: CreateJobRequest) -> str:
        """
        Create a Job.

        :param job_request: The CreateJobRequest
        :return: The ID of the created Job
        :raises JobCreationException: If the Job cannot be created
        :raises UnexpectedException: If an unexpected error occurs
        """
        try:
            self._logger.info(f"Creating job for Task(id={job_request.task_id})")
            job = Job(task_id=job_request.task_id, env_vars=job_request.env_vars)
            self._job_repo.add(job)
            return job.id
        except Exception as e:
            raise JobCreationException(
                f"Failed to create job for Task with ID:  {job_request.task_id}",
                e,
            )

    def get_status(self, job_id: str) -> JobStatus:
        """
        Retrieve the status of a Job.

        :param job_id: The ID of the Job
        :return: The status of the Job
        :raises JobNotFoundException: If the Job is not found
        :raises UnexpectedException: If an unexpected error occurs while retrieving the Job
        """

        self._logger.info(f"Getting Job(id={job_id})")
        try:
            job = self._job_repo.get(job_id)
        except Exception as e:
            raise UnexpectedException(f"Unexpected error getting Job(id={job_id})", e)

        if job is None:
            raise JobNotFoundException(f"Job(id={job_id}) not found")

        return job.status

    async def get_output(self, job_id: str, path: str) -> JobArtifact:
        """
        Get a file from a Job's output.

        :param job_id: The ID of the Job
        :param path: The path to the file within the Job's output
        :return: The contents of the file
        :raises JobNotFoundException: If the Job does not exist or has not been completed
        """
        job = self._job_repo.get(job_id)
        if job is None:
            raise JobNotFoundException(
                f"The output cannot be retrieved. Job(id={job_id}) not found",
            )
        elif job.status != JobStatus.SUCCEEDED:
            raise JobNotFoundException(
                "The output cannot be retrieved."
                f"Job(id={job_id}) has '{job.status}' status.",
            )
        else:
            return await self._get_job_output(job_id, path)

    def _get_job_artifact(self, job_id: str) -> Optional[JobArtifact]:
        """
        Retrieve a JobArtifact for a given job ID.

        :param job_id: The ID of the Job
        :return: The content of the JobArtifact if found, otherwise None
        :raises UnexpectedException: If an error occurs while retrieving the JobArtifact
        :raises JobArtifactNotFoundException: If no JobArtifact is found for the given job ID
        """

        try:
            job_artifact = self._artifact_repo.get_by_job_id(job_id)
        except Exception as e:
            raise UnexpectedException(f"Failed to get output from Job(id={job_id})", e)
        if job_artifact is None:
            raise JobArtifactNotFoundException(
                f"The output for Job(id={job_id}) was not found",
            )
        return job_artifact.content

    async def _get_job_output(self, job_id: str, path: Path) -> Optional[JobArtifact]:
        """
        Retrieve the content of a JobArtifact for a given job ID and path.

        :param job_id: The ID of the Job
        :param path: The path to the file within the Job's output
        :return: The content of the JobArtifact if found, otherwise None
        :raises JobArtifactNotFoundException: If no JobArtifact is found for the given job ID or path
        """
        job_artifact = self._artifact_repo.get_by_job_id(job_id)
        if job_artifact is None:
            raise JobArtifactNotFoundException(
                f"The output for Job(id={job_id}) was not found",
            )
        elif path not in job_artifact.output_path:
            raise JobArtifactNotFoundException(
                f"The path '{path}' was not found in the output of Job(id={job_id})",
            )
        else:
            return await job_utils.get_file_by_path(path)
