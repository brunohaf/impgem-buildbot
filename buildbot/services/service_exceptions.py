from loguru import Logger, logger


class ExceptionBase(Exception):
    """Base exception class."""

    _logger: Logger = logger

    def __init__(self, message: str, *args) -> None:
        self._logger.error(message)
        super().__init__(message, *args)


class UnexpectedException(ExceptionBase):
    """Exception raised when an unexpected error occurs."""


class JobNotFoundException(ExceptionBase):
    """Exception raised when a Job is not found."""


class TaskNotFoundException(ExceptionBase):
    """Exception raised when a Task is not found."""


class TaskCreationException(ExceptionBase):
    """Exception raised when a Task cannot be created."""


class TaskUpdateException(ExceptionBase):
    """Exception raised when a Task cannot be updated."""


class JobArtifactNotFoundException(ExceptionBase):
    """Exception raised when a JobArtifact is not found."""


class JobCreationException(ExceptionBase):
    """Exception raised when a Job cannot be created."""
