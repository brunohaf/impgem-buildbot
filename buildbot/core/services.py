from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from buildbot.core import utils
from buildbot.core.enums import DataContext
from buildbot.core.utils import SingletonMeta
from buildbot.data.schemas import Job
from buildbot.data.storage import Storage, get_storage
from buildbot.web.api.job.schema import (
    CreateJobRequest,
    CreateJobResponse,
    GetJobStatusResponse,
)


class TaskService(metaclass=SingletonMeta):

    def __init__(
        self,
        task_storage: Storage = Depends(get_storage(DataContext.TASK)),
    ) -> None:
        self._logger = logger
        self._task_storage = task_storage

    def create(self, task_id: str) -> None:
        self._logger.info(f"Creating task with ID: {task_id}")
        try:
            self._task_storage.add({"id": task_id})
        except Exception:
            self._logger.error(f"Failed to create task with ID: {task_id}")
            raise
        return

    def update(self, task_id: str) -> None:
        self._logger.info(f"Updating task with ID: {task_id}")
        try:
            self._task_storage.update({"id": task_id})
        except Exception:
            self._logger.error(f"Failed to update task with ID: {task_id}")
            raise
        return

    def get(self, task_id: str) -> None:
        self._logger.info(f"Getting task with ID: {task_id}")
        try:
            self._task_storage.get(task_id)
        except Exception:
            self._logger.error(f"Failed to get task with ID: {task_id}")
            raise
        return


class JobService(metaclass=SingletonMeta):

    def __init__(
        self,
        job_storage: Storage = Depends(get_storage(DataContext.JOB)),
    ) -> None:
        self._logger = logger
        self._job_storage = job_storage

    def create(self, job_request: CreateJobRequest) -> CreateJobResponse:
        try:
            self._logger.info(
                f"Creating job for Task with ID:"
                f"{job_request.task_id}"
            )
            job = Job(
                task_id=job_request.task_id,
                env_vars=job_request.env_vars
            )
            self._job_storage.add(job)
            return CreateJobResponse(job_id=job.id)
        except Exception:
            self._logger.error(
                f"Failed to create job for Task with ID: "
                f" {job_request.task_id}"
            )
            raise

    def get_status(self, job_id: str) -> GetJobStatusResponse:
        self._logger.info(f"Getting job with ID: {job_id}")
        try:
            job = self._job_storage.get(job_id)
        except Exception:
            self._logger.error(f"Unexpected error getting job with ID: {job_id}")
            raise

        if job is None:
            self._logger.error(f"Failed to get job with ID: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        return GetJobStatusResponse(status=job.status)

    async def get_output(self, job_id: str) -> str:
        job = self._job_storage.get(job_id)
        if job is None:
            self._logger.error(f"Failed to get job with ID: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            job_outputs = await utils.zip_folder(job.output_path)
            return FileResponse(job_outputs, media_type="application/zip")
        except Exception:
            self._logger.error(
                f"Failed to get output for job with ID: {job_id}"
            )
            raise


def get_task_service() -> TaskService:
    return TaskService()


def get_job_service() -> JobService:
    return JobService()
