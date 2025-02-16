"""Task service module."""

from app.services.task.service import (
    TaskService,
    get_task_service,
)

__all__ = [
    "get_task_service",
    "TaskService",
]
