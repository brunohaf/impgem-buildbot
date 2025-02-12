from abc import ABC
from typing import Optional

from buildbot.core.settings import settings
from buildbot.repository import redis_utils
from buildbot.repository.base_repository import BaseRedisRepository, BaseRepository
from buildbot.repository.job.schemas import Job
from buildbot.services.service_exceptions import JobCreationException


class JobRepository(ABC, BaseRepository):
    pass


class JobRedisRepository(JobRepository, BaseRedisRepository):
    """Redis-backed Job Repository."""

    def _get_key(self, id):
        return f"job:${id}"

    # ? Separation of concerns is not ideal here for simplicity's sake.
    # ? A set(ssad) is created for each task for efficient job lookup
    # ? when retrieving jobs.envVars for running task.script.
    # ? The set would be used for batching remove jobs if the task is deleted.
    # ? correlating tasks and jobs should be done at database level,
    # ? or a JobTask facade at the service layer.
    async def create(self, job: Job) -> None:
        """Creates a new Job in Redis."""

        task_exists = await self._redis.exists(
            redis_utils.get_task_key(job.task_id)
        )

        if not task_exists:
            self._logger.warning(
                f"Failed to create Job(id={job.id})."
                f" Task(id={job.task_id}) was not found."
            )
            return

        job_data = job.model_dump_json()
        async with self._redis.pipeline() as pipe:
            job_key = self._get_key(job.id)
            await pipe.set(job_key, job_data).sadd(
                redis_utils.get_task_jobs_key(job.task_id), job_key
            )

    async def get(self, id: str) -> Optional[Job]:
        """Retrieves a Job by ID."""
        job_data = await self._redis.get(redis_utils.get_key(Job(id=id)))
        job = Job.model_validate_json(job_data) if job_data else None
        if (job is None):
            self._logger.warning(f"Could not retrieve Job(id={id})")
            return
        return job


# ? A RepositoryType enum and a factory function
# ? could streamline this for future implementations of JobRepository.
async def get_job_repository() -> JobRepository:
    """Returns the singleton JobRedisRepository."""
    return await JobRedisRepository.initialize(settings.redis.get_url())
