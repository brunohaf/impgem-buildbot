from typing import Optional

from app.core.settings import settings
from app.repository import utils
from app.repository.job.schemas import Job
from app.repository.repository import BaseRedisRepository, BaseRepository


class JobRepository(BaseRepository):
    """Abstract Job Repository."""


class JobRedisRepository(JobRepository, BaseRedisRepository):
    """Redis-backed Job Repository."""

    def _get_key(self, id: str) -> str:
        return f"job:${id}"

    async def create(self, job: Job) -> Optional[str]:
        """Creates a new Job in Redis."""
        task_exists = await self._redis.exists(utils.get_task_key(job.task_id))
        if not task_exists:
            self._logger.warning(
                f"Failed to create Job(id={job.id})."
                f" Task(id={job.task_id}) was not found.",
            )
            return None

        job_data = job.model_dump_json()
        job_key = self._get_key(job.id)
        await self._redis.set(job_key, job_data)
        return job.id

    async def get(self, id: str) -> Optional[Job]:
        """Retrieves a Job by ID."""
        job_data = await self._redis.get(utils.get_key(Job(id=id)))
        job = Job.model_validate_json(job_data) if job_data else None
        if job is None:
            self._logger.warning(f"Could not retrieve Job(id={id})")
            return None
        return job

    # ? Separation of concerns is not ideal here for simplicity's sake.
    # ? A set(ssad) is created for each task for efficient job lookup
    # ? when retrieving jobs.envVars for running task.script.
    # ? The set would be used for batching remove jobs if the task is deleted.
    # ? correlating tasks and jobs should be done at database level,
    # ? or a JobTask facade at the service layer.
    async def associate_job_with_task(
        self,
        job_id: str,
        task_id: str,
    ) -> Optional[str]:
        """Associates a Job with a Task by ID."""
        job_key = self._get_key(job_id)
        await self._redis.sadd(utils.get_task_jobs_key(task_id), job_key)


# ? A RepositoryType enum and a factory function
# ? could streamline this for future implementations of JobRepository.
def get_job_repository() -> JobRepository:
    """Returns the singleton JobRedisRepository."""
    return JobRedisRepository.initialize(settings.redis.get_url())
