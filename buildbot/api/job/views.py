from pathlib import Path

from fastapi import APIRouter, Depends

from buildbot.api.job.schema import (
    CreateJobRequest,
    CreateJobResponse,
    GetJobStatusResponse,
)
from buildbot.services.job_service import JobService

router = APIRouter()


@router.post("/", response_model=CreateJobResponse, tags=["job"])
async def create_job(
    job_request: CreateJobRequest,
    job_svc: JobService = Depends(),
) -> CreateJobResponse:
    """Create a Job."""
    return CreateJobResponse(job_id=await job_svc.create(job_request))


@router.get("/{job_id}/status", tags=["job"])
async def get_job_status(
    job_id: str,
    job_svc: JobService = Depends(),
) -> GetJobStatusResponse:
    """Get the status of a Job."""
    return GetJobStatusResponse(status=await job_svc.get_status(job_id))


@router.get("/{job_id}/output/{path}", tags=["job"])
async def get_job_output(
    job_id: str,
    path: Path,
    job_svc: JobService = Depends(),
) -> bytes:
    """Get a file from a Job's output.

    :param job_id: The ID of the Job
    :param path: The path to the file within the Job's output
    :return: The contents of the file
    """

    return await job_svc.get_output(job_id, path)
