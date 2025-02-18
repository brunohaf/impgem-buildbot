from typing import Dict

import taskiq_fastapi
from app.background import job_manager
from taskiq import AsyncBroker, InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from buildbot.app.core.settings import settings

SCHEDULE: str = [{"cron": settings.job_manager.container_manager_schedule}]

broker: AsyncBroker = InMemoryBroker()
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.task(schedule=SCHEDULE)
async def check_jobs_status() -> None:
    """Pings for the containers status every X minutes."""
    await job_manager.manage_containers()


@broker.task
async def run_job(job_id: str, script: str, env_vars: Dict[str, str]) -> None:
    """Runs a Task in a Docker container."""
    await job_manager.run_job(job_id, script, env_vars)


taskiq_fastapi.init(
    broker,
    "app.api.application:get_app",
)
