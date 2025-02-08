from pydantic import BaseModel, field_validator


@field_validator("script", mode="before")
class CreateTaskRequest(BaseModel):
    """Task request model."""

    script: str


class CreateTaskResponse(BaseModel):
    """Task response model."""

    task_id: str


class GetTaskResponse(BaseModel):
    """Task response model."""

    script: str


@field_validator("script", mode="before")
class UpdateTaskRequest(BaseModel):
    """Task request model."""

    script: str
