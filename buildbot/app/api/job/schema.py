from pydantic import BaseModel


class CreateJobResponse(BaseModel):
    """Job response model."""

    job_id: str


class GetJobStatusResponse(BaseModel):
    """Job status response model."""

    status: str
