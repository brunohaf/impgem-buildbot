def get_task_jobs_key(task_id: str) -> str:
    """Returns a Redis key for a Task's Jobs set."""
    return f"task:{task_id}:jobs"
