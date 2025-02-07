from enum import StrEnum


class DataContext(StrEnum):
    """
    Enum for data context.
    """

    TASK = "task"
    JOB = "job"


class JobStatus(StrEnum):
    """
    Enum for job status.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
