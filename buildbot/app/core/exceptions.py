from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Optional

import loguru


class BaseError(Exception):
    """Base Error class."""

    _logger: loguru.Logger = loguru.logger
    message: str = ""

    @abstractmethod
    def _format_message(self, *args: object) -> str:
        pass

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


class JobNotFoundError(BaseError):
    """Error raised when a Job is not found."""

    def __init__(self, job_id: str, *args: object) -> None:
        self.message = self._format_message(job_id)
        super().__init__(self.message, *args)

    def _format_message(self, job_id: str) -> str:
        return f"The Job(id={job_id}) was not found."


class JobCreationError(BaseError):
    """Error raised when a Job cannot be created."""

    def __init__(self, task_id: Optional[str], *args: object) -> None:
        self.message = self._format_message(task_id)
        super().__init__(self.message, *args)

    def _format_message(self, task_id: Optional[str]) -> str:
        if task_id:
            return f"Could not create Job. Task(id={task_id}) not found."
        return f"Could not create Job. {self.__cause__!s}."


class JobSchedulingError(BaseError):
    """Error raised when a Job cannot be scheduled."""

    def __init__(self, *args: object) -> None:
        self.message = self._format_message()
        super().__init__(self.message, *args)

    def _format_message(self) -> str:
        return "Could not schedule the Job."


class JobNotCompletedError(BaseError):
    """Error raised when a Job has not completed."""

    def __init__(self, job_id: str, job_status: str, *args: object) -> None:
        self.message = self._format_message(job_id, job_status)
        super().__init__(self.message, *args)

    def _format_message(self, job_id: str, job_status: str) -> str:
        return f"The Job(id={job_id}) has status '{job_status}'."


class JobFailedError(BaseError):
    """Error raised when a Job has failed."""

    def __init__(self, job_id: str, *args: object) -> None:
        self.message = self._format_message(job_id)
        super().__init__(self.message, *args)

    def _format_message(self, job_id: str) -> str:
        return f"The Job(id={job_id}) execution failed."


class JobOutputAccessDeniedError(BaseError):
    """Error raised when the requested Job Output is forbidden."""

    def __init__(self, job_id: str, *args: object) -> None:
        self.message = self._format_message(job_id)
        super().__init__(self.message, *args)

    def _format_message(self, job_id: str, path: Path) -> str:
        return f"The path '{path}' is not on the Job(id={job_id}) directory."


class JobOutputNotFoundError(BaseError):
    """Error raised when the requested Job Output is not found."""

    def __init__(self, job_id: str, path: Path, *args: object) -> None:
        self.message = self._format_message(job_id, path)
        super().__init__(self.message, *args)

    def _format_message(self, job_id: str, path: Path) -> str:
        return (
            f"No such file or directory. The path '{path}'"
            f" was not found on the Job(id={job_id}) directory."
        )


class TaskNotFoundError(BaseError):
    """Error raised when a Task is not found."""

    def __init__(self, task_id: str, *args: object) -> None:
        self.message = self._format_message(task_id)
        super().__init__(self.message, *args)

    def _format_message(self, task_id: str) -> str:
        return f"The Task(id={task_id}) was not found."


class TaskCreationError(BaseError):
    """Error raised when a Task cannot be created."""

    def __init__(self, *args: object) -> None:
        self.message = self._format_message()
        super().__init__(*args)

    def _format_message(self) -> str:
        return "Could not create the Task."


class TaskNotUpdatedError(BaseError):
    """Error raised when a Task cannot be updated."""

    def __init__(self, task_id: str, *args: object) -> None:
        self.message = self._format_message(task_id)
        super().__init__(self.message, *args)

    def _format_message(self, task_id: str) -> str:
        return f"The Task(id={task_id}) was not updated."
