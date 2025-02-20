import taskiq_fastapi
from app.background.job_manager.container import (
    ContainerJobManager,
    get_container_manager,
)
from app.core.settings import settings
from taskiq import AsyncBroker, InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

SCHEDULE: str = [{"cron": settings.job_manager_settings.schedule}]

broker: AsyncBroker = InMemoryBroker()
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)

job_manager: ContainerJobManager = get_container_manager()


@broker.task(schedule=SCHEDULE)
async def manage_jobs() -> None:
    """Manage Jobs in background."""
    await job_manager.manage_jobs()


taskiq_fastapi.init(
    broker,
    "app.api.application:get_app",
)
