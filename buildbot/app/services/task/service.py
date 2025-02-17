from abc import ABC, abstractmethod
from typing import Optional

from app.core.exceptions import (
    TaskCreationError,
    TaskNotFoundError,
    TaskNotUpdatedError,
)
from app.repository.task.repository import TaskRepository, get_task_repository
from app.repository.task.schemas import Task
from app.services.task.schema import TaskDTO
from fastapi import Depends
from loguru import logger


class TaskQueryService(ABC):
    """Service for Task query operations."""

    @abstractmethod
    async def get(self, task_id: str) -> Task:
        """Retrieves a Task by ID."""


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
        :raises TaskCreationError: If the Task cannot be created
        """
        try:
            task = Task(script=self._sanitize_bash_script(task_dto.script))
            await self._task_repo.create(task)
            return task.id
        except Exception as e:
            raise TaskCreationError from e

    async def update(self, task_id: str, task_dto: TaskDTO) -> str:
        """
        Updates existing Task.

        :param task_id: The ID of the Task
        :return: The ID of the Task
        :raises TaskNotFoundError: If the Task cannot be updated
        """
        was_updated = (
            await self._task_repo.update(
                Task(id=task_id, script=task_dto.script),
            )
        ) or False

        if not was_updated:
            raise TaskNotUpdatedError(task_id)
        return task_id

    async def get(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a Task by its ID.

        :param task_id: The ID of the Task
        :return: Retrieved Task
        :raises TaskNotFoundError: If the Task does not exist
        """
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        return task

    def _sanitize_bash_script(self, script: str) -> str:
        """Sanitizes a bash script."""
        shebang = "#!/bin/sh"
        if not script.startswith(shebang):
            script = f"{shebang}\n{script}"
        return script


task_service: TaskService = TaskService()


def get_task_service() -> TaskService:
    """Returns a TaskService instance."""
    return task_service


def get_task_query_service() -> TaskQueryService:
    """Returns a TaskService instance."""
    return task_service
