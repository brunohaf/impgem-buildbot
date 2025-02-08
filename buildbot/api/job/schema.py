from typing import Dict

from pydantic import BaseModel, field_validator


@field_validator("task_id", mode="before")
class CreateJobRequest(BaseModel):
    """Job request model."""

    task_id: str
    env_vars: Dict[str, str] = {}


class CreateJobResponse(BaseModel):
    """Job response model."""

    job_id: str


class GetJobStatusResponse(BaseModel):
    """Job status response model."""

    status: str
