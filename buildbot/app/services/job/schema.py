from typing import Dict

from pydantic import BaseModel, field_validator


@field_validator("task_id", mode="before")
class JobDTO(BaseModel):
    """Job request model."""

    task_id: str
    env_vars: Dict[str, str] = {}
