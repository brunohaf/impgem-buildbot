from __future__ import annotations

from typing import Any

import loguru


class ExceptionBase(Exception):
    """Base exception class."""

    _logger:  loguru.Logger = loguru.logger

    def __init__(self, message: str, *args: Any) -> None:
        self._logger.error(message)

        super().__init__(message, *args)


class UnexpectedException(ExceptionBase):
    """Exception raised when an unexpected error occurs."""
    pass


class JobNotFoundException(ExceptionBase):
    """Exception raised when a Job is not found."""
    pass


class JobCreationException(UnexpectedException):
    """Exception raised when a Job cannot be created."""
    pass


class JobNotCompletedException(ExceptionBase):
    """Exception raised when a Job has not completed."""
    pass


class JobFailedException(ExceptionBase):
    """Exception raised when a Job has failed."""
    pass


class JobOutputAccessDeniedException(ExceptionBase):
    """Exception raised when the requested Job Output is forbidden."""
    pass


class TaskNotFoundException(ExceptionBase):
    """Exception raised when a Task is not found."""
    pass


class TaskCreationException(UnexpectedException):
    """Exception raised when a Task cannot be created."""
    pass


class TaskUpdateException(ExceptionBase):
    """Exception raised when a Task cannot be updated."""
    pass
