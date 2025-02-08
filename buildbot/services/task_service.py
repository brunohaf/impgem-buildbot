from fastapi import Depends
from loguru import logger

from buildbot.api.task.schema import CreateTaskRequest, UpdateTaskRequest
from buildbot.repository.task.repository import TaskRepository, get_task_repository
from buildbot.repository.task.schemas import Task
from buildbot.services.service_exceptions import (
    TaskCreationException,
    TaskNotFoundException,
)


class TaskService:
    """Service for Task operations."""

    def __init__(
        self,
        task_repo: TaskRepository = Depends(get_task_repository),
    ) -> None:
        self._logger = logger
        self._task_repo = task_repo

    def create(self, task_request: CreateTaskRequest) -> str:
        """
        Creates a new Task.

        :param task_request: The CreateTaskRequest
        :return: The ID of the Task
        :raises TaskCreationException: If the Task cannot be created
        """
        task = Task(script=task_request.script)
        try:
            self._task_repo.create(task)
        except Exception as e:
            raise TaskCreationException(f"Failed to create Task(id={task.id})", e)
        return task.id

    def update(
        self, task_id: str, task_request: UpdateTaskRequest
    ) -> str:
        """
        Updates existing Task.

        :param task_id: The ID of the Task
        :return: The ID of the Task
        :raises TaskUpdateException: If the Task cannot be updated
        :raises UnexpectedException: If an unexpected error occurs
        """
        self._task_repo.update(Task(id=task_id, script=task_request.script))
        return task_id

    def get(self, task_id: str) -> Task:
        """
        Retrieve a Task by its ID.

        :param task_id: The ID of the Task
        :return: Retrieved Task
        :raises TaskNotFoundException: If the Task does not exist
        """
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundException(f"Task(id={task_id}) not found")
        return task
