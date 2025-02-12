from abc import ABC, abstractmethod

from fastapi import Depends
from loguru import logger

from buildbot.repository.task.base_repository import TaskRepository, get_task_repository
from buildbot.repository.task.schemas import Task
from buildbot.services.service_exceptions import (
    TaskCreationException,
    TaskNotFoundException,
)
from buildbot.services.task.schema import TaskDTO


class TaskQueryService(ABC):
    """Service for Task query operations."""
    @abstractmethod
    async def get(self, task_id: str) -> Task:
        pass


class TaskService(TaskQueryService):
    """Service for Task operations."""

    def __init__(
        self,
        task_repo: TaskRepository = Depends(get_task_repository),
    ) -> None:
        self._logger = logger
        self._task_repo = task_repo

    async def create(self, task_dto: TaskDTO) -> str:
        """
        Creates a new Task.

        :param task_dto: The CreateTaskRequest
        :return: The ID of the Task
        :raises TaskCreationException: If the Task cannot be created
        """
        task = Task(script=task_dto.script)
        try:
            await self._task_repo.create(task)
        except Exception as e:
            raise TaskCreationException(f"Failed to create Task(id={task.id})", e)
        return task.id

    async def update(self, task_id: str, task_dto: TaskDTO) -> str:
        """
        Updates existing Task.

        :param task_id: The ID of the Task
        :return: The ID of the Task
        :raises TaskUpdateException: If the Task cannot be updated
        :raises UnexpectedException: If an unexpected error occurs
        """
        await self._task_repo.update(Task(id=task_id, script=task_dto.script))
        return task_id

    async def get(self, task_id: str) -> Task:
        """
        Retrieve a Task by its ID.

        :param task_id: The ID of the Task
        :return: Retrieved Task
        :raises TaskNotFoundException: If the Task does not exist
        """
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundException(f"Task(id={task_id}) not found")
        return task


def get_task_query_service() -> TaskQueryService:
    return TaskService()
