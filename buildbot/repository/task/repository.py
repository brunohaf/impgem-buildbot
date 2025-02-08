from abc import ABC, abstractmethod
from asyncio import Task
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import SingletonMeta


class TaskRepository(ABC):
    """Interface for Task repository implementation classes."""

    @abstractmethod
    def add(self, task: Task) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[Task]:
        pass

    @abstractmethod
    def update(self, new_task: Task) -> Optional[Task]:
        pass


class TaskInMemoryRepository(TaskRepository, metaclass=SingletonMeta):
    """In-memory Task Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, Task] = {}
        self._logger = logger

    def add(self, entity: Task) -> None:
        """Add a Task to the repository."""
        self._storage[entity.id] = entity

    def get(self, id: str) -> Optional[Task]:
        """Retrieve a Task by its ID."""
        return self._storage.get(id)

    def update(self, new_task: Task) -> Optional[Task]:
        """Updates existing Task."""

        if self._storage.get(new_task.id) is None:
            self._logger.info(
                f"Failed to update Task(id={new_task.id}) because it doesn't exist",
            )
            return None

        self._storage[new_task.id] = new_task
        self._logger.info(f"Successfully updated Task(id={new_task.id})")

        return new_task


def get_task_repository() -> TaskRepository:
    return TaskInMemoryRepository()
