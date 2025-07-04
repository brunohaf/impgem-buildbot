from pathlib import Path
from typing import List

from app.api.job.schema import CreateJobResponse, GetJobStatusResponse
from app.core.exceptions import (
    JobCreationError,
    JobFailedError,
    JobNotCompletedError,
    JobNotFoundError,
    JobOutputNotFoundError,
    TaskNotFoundError,
)
from app.services.job import JobService
from app.services.job.schema import JobDTO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

router = APIRouter()

_tags: List[str] = ["job"]


@router.post(
    "/",
    response_model=CreateJobResponse,
    status_code=status.HTTP_201_CREATED,
    tags=_tags,
)
async def create_job(
    job_request: JobDTO,
    job_svc: JobService = Depends(),
) -> CreateJobResponse:
    """
    Create a Job.

    :param job_request: The CreateJobRequest
    :return: The ID of the created Job
    """
    try:
        job_id = await job_svc.create(job_request)
        return CreateJobResponse(job_id=job_id)
    except JobCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{job_id}/status", tags=_tags)
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
        job_status = await job_svc.get_status(job_id)
        return GetJobStatusResponse(status=job_status)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{job_id}/output/{file_path}", tags=_tags)
async def get_job_output(
    job_id: str,
    file_path: Path,
    job_svc: JobService = Depends(),
) -> StreamingResponse:
    """Get a file from a Job's output.

    :param job_id: The ID of the Job
    :param file_path: The path to the file within the Job's output
    :raise HTTPException: If the Job does not exist or is not completed
    :return: The contents of the file
    """
    try:
        return await job_svc.get_output(job_id, file_path)
    except JobOutputNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot retrieve the output. Not found.",
        ) from e
    except JobNotCompletedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT) from e
    except JobFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot retrieve the output. The Job has failed.",
        ) from e
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except TaskNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from e
