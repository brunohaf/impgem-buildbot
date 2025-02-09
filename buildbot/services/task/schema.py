from pydantic import BaseModel, field_validator


@field_validator("script", mode="before")
class TaskDTO(BaseModel):
    """Task DTO."""

    script: str
