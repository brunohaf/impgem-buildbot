from typing import Dict

import taskiq_fastapi
from app.background.job_manager.container import ContainerManager, get_container_manager
from app.core.settings import settings
from taskiq import AsyncBroker, InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

SCHEDULE: str = [{"cron": settings.job_manager.manager_schedule}]

broker: AsyncBroker = InMemoryBroker()
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)

job_manager: ContainerManager = get_container_manager()


@broker.task(schedule=SCHEDULE)
async def manage_jobs() -> None:
    """Manage Jobs in background."""
    await job_manager.manage_jobs()


@broker.task
async def process(job_id: str, script: str, env_vars: Dict[str, str]) -> None:
    """Process a Job."""
    await job_manager.process(job_id, script, env_vars)


taskiq_fastapi.init(
    broker,
    "app.api.application:get_app",
)
