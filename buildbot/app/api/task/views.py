from typing import List

from app.api.task.schema import (
    CreateTaskResponse,
    GetTaskResponse,
    UpdateTaskResponse,
)
from app.core.exceptions import TaskNotFoundError
from app.services.task import TaskService
from app.services.task.schema import TaskDTO
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

_tags: List[str] = ["task"]


@router.post(
    "/",
    response_model=CreateTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task: TaskDTO,
    task_svc: TaskService = Depends(),
) -> CreateTaskResponse:
    """
    Create a Task.

    :param task: The CreateTaskRequest
    :return: The ID of the created Task
    """
    task_id = await task_svc.create(task)
    return CreateTaskResponse(task_id=task_id)


@router.get("/", response_model=GetTaskResponse, tags=_tags)
async def get_task(
    task_id: str,
    task_svc: TaskService = Depends(),
) -> GetTaskResponse:
    """
    Retrieve a Task by its ID.

    :param task_id: The ID of the Task
    :return: The retrieved Task
    :raises TaskNotFoundError: If the Task does not exist
    """
    try:
        task = await task_svc.get(task_id)
        return GetTaskResponse(script=task.script)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e


@router.put(
    "/",
    response_model=UpdateTaskResponse,
    status_code=status.HTTP_200_OK,
    tags=_tags,
)
async def update_task(
    task_id: str,
    task: TaskDTO,
    task_svc: TaskService = Depends(),
) -> UpdateTaskResponse:
    """
    Updates existing Task.

    :param task_id: The ID of the Task
    :return: The ID of the Task
    :raises TaskUpdateException: If the Task cannot be updated
    :raises UnexpectedException: If an unexpected error occurs
    """
    try:
        task_id = await task_svc.update(task_id, task)
        return UpdateTaskResponse(task_id=task_id)
    except TaskNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from e
