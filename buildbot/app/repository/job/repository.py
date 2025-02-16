from abc import abstractmethod
from typing import Optional

from app.core.settings import settings
from app.repository.job.schemas import Job, JobStatus
from app.repository.repository import BaseRedisRepository, BaseRepository


class JobRepository(BaseRepository):
    """Abstract Job Repository."""

    @abstractmethod
    async def create(self, job: Job) -> Optional[str]:
        """Creates a new Job in Redis."""

    @abstractmethod
    async def get(self, id: str) -> Optional[Job]:
        """Retrieves a Job by ID."""

    @abstractmethod
    async def update(self, new_job: Job) -> Optional[str]:
        """Updates an existing job in Redis."""

    @abstractmethod
    async def update_status(self, job_id: str, status: str) -> Optional[str]:
        """Updates the status of a Job."""

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Deletes a Job by ID."""


# ? Separation of concerns is not ideal here for simplicity's sake.
# ? A set(ssad) is created for each task for efficient job lookup
# ? when retrieving jobs.envVars for running task.script.
# ? The set would be used for batching remove jobs if the task is deleted.
# ? correlating tasks and jobs should be done at database level,
# ? or a JobTask facade at the service layer.
class JobRedisRepository(JobRepository, BaseRedisRepository):
    """Redis-backed Job Repository."""

    def _get_key(self, id: str) -> str:
        return f"job:{id}"

    def _get_task_key(self, id: str) -> str:
        return f"task:{id}"

    async def create(self, job: Job) -> Optional[str]:
        """Creates a new Job in Redis."""
        await self._redis.set(self._get_key(job.id), job.model_dump_json())
        return job.id

    async def get(self, id: str) -> Optional[Job]:
        """Retrieves a Job by ID."""
        job_data = await self._redis.get(self._get_key(id))
        job = Job.model_validate_json(job_data) if job_data else None
        if job is None:
            self._logger.warning(f"Could not retrieve Job(id={id})")
            return None
        return job

    async def update(self, new_job: Job) -> Optional[str]:
        """Updates an existing job in Redis."""
        job_key = self._get_key(new_job.id)
        job_data = await self._redis.get(job_key)
        if job_data is None:
            self._logger.warning(
                f"Failed to update Job(id={new_job.id}). Not found",
            )
            return None

        updated_job = Job.model_validate(
            {
                **Job.model_validate_json(job_data).model_dump(exclude_unset=True),
                **new_job.model_dump(exclude_unset=True),
            },
        )

        await self._redis.set(job_key, updated_job.model_dump_json())
        return new_job.id

    async def update_status(self, job_id: str, status: JobStatus) -> Optional[str]:
        """Updates the status of a Job."""
        job = await self.get(job_id)
        if not job:
            return None
        job.status = status
        return await self.update(job)

    async def delete(self, id: str) -> None:
        """Deletes a Job by ID."""
        await self._redis.delete(self._get_key(id))


# ? A RepositoryType enum and a factory function
# ? could streamline this for future implementations of JobRepository.
def get_job_repository() -> JobRepository:
    """Returns the singleton JobRedisRepository."""
    return JobRedisRepository.initialize(settings.redis.get_url())
