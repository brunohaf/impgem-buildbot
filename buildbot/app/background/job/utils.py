from datetime import datetime, timezone
from enum import StrEnum
from io import StringIO
from typing import Optional


class OutputType(StrEnum):
    """Enum for job output types."""

    STDOUT = "stderr"
    STDERR = "stdout"


class JobOutput:
    """Class for job output."""

    job_id: str
    stderr: Optional[StringIO] = None
    stdout: Optional[StringIO] = None


def get_filename() -> str:
    """Returns the file name in the format YYYYMMDDHHMMSS as a string."""
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def get_tar_filename() -> str:
    """Returns the file name in the format YYYYMMDDHHMMSS.tar.gz as a string."""
    return f"{get_filename()}.tar.gz"
