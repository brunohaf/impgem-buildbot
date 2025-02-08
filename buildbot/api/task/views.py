from fastapi import APIRouter, Depends, HTTPException

from buildbot.api.task.schema import (
    CreateTaskRequest,
    CreateTaskResponse,
    GetTaskResponse,
    UpdateTaskResponse,
)
from buildbot.services.service_exceptions import TaskNotFoundException
from buildbot.services.task_service import TaskService

router = APIRouter()


@router.post("/", response_model=CreateTaskResponse)
async def create_task(
    task: CreateTaskRequest,
    task_svc: TaskService = Depends(),
) -> CreateTaskResponse:
    """
    Create a Task.

    :param task: The CreateTaskRequest
    :return: The ID of the created Task
    """
    return CreateTaskResponse(task_svc.create(task))


@router.get("/", response_model=CreateTaskResponse)
async def get_task(
    task_id: str,
    task_svc: TaskService = Depends(),
) -> GetTaskResponse:
    """
    Retrieve a Task by its ID.

    :param task_id: The ID of the Task
    :return: The retrieved Task
    :raises TaskNotFoundException: If the Task does not exist
    """
    try:
        task = task_svc.get(task_id)
        return GetTaskResponse(script=task.script)
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/", response_model=UpdateTaskResponse)
async def update_task(
    task_id: str,
    task: CreateTaskRequest,
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
        return UpdateTaskResponse(task_svc.update(task_id, task))
    except TaskNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
