from typing import Optional

from buildbot.repository.base_repository import BaseRedisRepository
from buildbot.repository.task.schemas import Task


class TaskRedisRepository(BaseRedisRepository):
    """Redis-backed Task Repository."""

    def _get_key(self, id: str) -> str:
        """Returns a Redis key for a Task."""
        return f"task:{id}"

    async def create(self, task: Task) -> None:
        """Creates a new Task in Redis."""
        await self._redis.set(self._get_key(task.id), task.model_dump_json())

    async def get(self, id: str) -> Optional[Task]:
        """Retrieves a Task by ID."""
        task_data = await self._redis.get(self._get_key(id))
        task = Task.model_validate_json(task_data) if task_data else None
        if task is None:
            self._logger.warning(f"Could not retrieve Task(id={id})")
            return
        return task

    async def update(self, new_task: Task) -> None:
        """Updates an existing task in Redis."""
        task_data = await self._redis.get(new_task.id)
        if task_data is None:
            self._logger.warning(
                f"Failed to update Task(id={new_task.id}). Not found"
            )
            return None

        updated_task_data = Task.model_validate(
            {
                **Task.model_validate_json(task_data),
                **new_task.model_dump(exclude_unset=True),
            }.model_dump_json()
        )
        await self._redis.set(new_task.id, updated_task_data)
