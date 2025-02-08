from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from buildbot.api.job.schema import (
    CreateJobRequest,
    CreateJobResponse,
    GetJobStatusResponse,
)
from buildbot.services.job_service import JobService
from buildbot.services.service_exceptions import (
    JobFailedException,
    JobNotCompletedException,
    JobNotFoundException,
    JobOutputAccessDeniedException,
)

router = APIRouter()


@router.post("/", response_model=CreateJobResponse, tags=["job"])
async def create_job(
    job_request: CreateJobRequest,
    job_svc: JobService = Depends(),
) -> CreateJobResponse:
    """
    Create a Job.

    :param job_request: The CreateJobRequest
    :return: The ID of the created Job
    """
    return CreateJobResponse(job_id=job_svc.create(job_request))


@router.get("/{job_id}/status", tags=["job"])
async def get_job_status(
    job_id: str,
    job_svc: JobService = Depends(),
) -> GetJobStatusResponse:
    """
    Retrieve the status of a Job.

    :param job_id: The ID of the Job
    :return: The status of the Job
    :raises HTTPException: If the Job is not found
    """
    try:
        job_svc.get_status(job_id)
        return GetJobStatusResponse(status=job_svc.get_status(job_id))
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")


@router.get("/{job_id}/output/{path}", tags=["job"])
async def get_job_output(
    job_id: str,
    path: Path,
    job_svc: JobService = Depends(),
) -> StreamingResponse:
    """Get a file from a Job's output.

    :param job_id: The ID of the Job
    :param path: The path to the file within the Job's output
    :raise HTTPException: If the Job does not exist or is not completed
    :return: The contents of the file
    """
    try:
        job_svc.get_status(job_id)
        job_output = await job_svc.get_output(job_id, path)
        return StreamingResponse(content=job_output)
    except JobOutputAccessDeniedException:
        raise HTTPException(status_code=403, detail="Access denied")
    except JobNotCompletedException:
        raise HTTPException(status_code=409, detail="Job not completed yet")
    except JobFailedException:
        raise HTTPException(
            status_code=410, detail="Job failed due to internal error"
        )
    except JobNotFoundException:
        raise HTTPException(status_code=404, detail="Job not found")
