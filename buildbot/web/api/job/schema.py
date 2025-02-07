from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    """Job request model."""

    task_id: str


class CreateJobResponse(BaseModel):
    """Job response model."""

    job_id: str


class GetJobStatusResponse(BaseModel):
    """Job status response model."""

    status: str
