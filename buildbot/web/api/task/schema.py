from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    """Task request model."""

    script: str


class CreateTaskResponse(BaseModel):
    """Task response model."""

    taskId: str


class GetTaskResponse(BaseModel):
    """Task response model."""

    script: str


class UpdateTaskRequest(BaseModel):
    """Task request model."""

    script: str
