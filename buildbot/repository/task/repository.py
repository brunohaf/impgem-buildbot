import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Dict, Optional

from loguru import logger

from buildbot.core.utils import SingletonMeta


class TaskRepository(ABC):
    """Interface for Task repository implementation classes."""

    @abstractmethod
    def create(self, task: Task) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[Task]:
        pass

    @abstractmethod
    def update(self, new_task: Task) -> None:
        pass


class TaskInMemoryRepository(TaskRepository, metaclass=SingletonMeta):
    """In-memory Task Repository Singleton."""

    def __init__(self):
        self._storage: Dict[str, Task] = {}
        self._logger = logger
        self._lock = asyncio.Lock()

    async def create(self, task: Task) -> None:
        """Add a Task to the repository."""
        self._logger.info(f"Creating Task(id={task.id})")
        async with self._lock:
            self._storage[task.id] = task
        self._logger.info(f"Task(id={task.id}) successfully created.")
        return

    def get(self, id: str) -> Optional[Task]:
        """Retrieve a Task by its ID."""
        self._logger.info(f"Getting Task(id={id})")
        task = self._storage.get(id)
        if task is None:
            self._logger.info(f"Cannot retrieve Task(id={id}). Not found")
        self._logger.info(f"Successfully retrieved Task(id={id})")
        return task

    async def update(self, new_task: Task) -> None:
        """Updates existing Task."""
        self._logger.info(f"Updating Task(id={new_task.id})")
        async with self._lock:
            if self._storage.get(new_task.id) is None:
                self._logger.info(f"Failed to update Task(id={id}). Not found")
            self._storage[new_task.id] = new_task
        self._logger.info(f"Successfully updated Task(id={new_task.id})")
        return


def get_task_repository() -> TaskRepository:
    return TaskInMemoryRepository()
