from typing import Optional

from app.core.settings import settings
from app.repository.repository import BaseRedisRepository, BaseRepository
from app.repository.task.schemas import Task


class TaskRepository(BaseRepository):
    """Abstract Task Repository."""


class TaskRedisRepository(TaskRepository, BaseRedisRepository):
    """Redis-backed Task Repository."""

    def _get_key(self, id: str) -> str:
        """Returns a Redis key for a Task."""
        return f"task:{id}"

    async def create(self, task: Task) -> str:
        """Creates a new Task in Redis."""
        await self._redis.set(self._get_key(task.id), task.model_dump_json())

    async def get(self, id: str) -> Optional[Task]:
        """Retrieves a Task by ID."""
        task_data = await self._redis.get(self._get_key(id))
        task = Task.model_validate_json(task_data) if task_data else None
        if task is None:
            self._logger.warning(f"Could not retrieve Task(id={id})")
            return None
        return task

    async def update(self, new_task: Task) -> Optional[str]:
        """Updates an existing task in Redis."""
        task_data = await self._redis.get(new_task.id)
        if task_data is None:
            self._logger.warning(
                f"Failed to update Task(id={new_task.id}). Not found",
            )
            return None

        updated_task_data = Task.model_validate(
            {
                **Task.model_validate_json(task_data),
                **new_task.model_dump(exclude_unset=True),
            }.model_dump_json(),
        )
        await self._redis.set(new_task.id, updated_task_data)
        return new_task.id

    async def delete(self, id: str) -> None:
        """Deletes a Task by ID."""


# ? A RepositoryType enum and a factory function
# ? could streamline this for future implementations of TaskRepository.
def get_task_repository() -> TaskRepository:
    """Returns the singleton TaskRedisRepository."""
    return TaskRedisRepository.initialize(settings.redis.get_url())
