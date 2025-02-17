from typing import Dict

import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from buildbot.app.background import job_manager

broker: AsyncBroker = InMemoryBroker()
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.task(schedule=[{"cron": "*/5 * * * *"}])
async def check_jobs_status() -> None:
    """Pings for the containers status every X minutes."""
    print("triggered!!!")
    await job_manager.check_container_status()


@broker.task
async def run_job(job_id: str, script: str, env_vars: Dict[str, str]) -> None:
    """Runs a Task in a Docker container."""
    await job_manager.run_job_in_container(job_id, script, env_vars)


taskiq_fastapi.init(
    broker,
    "app.api.application:get_app",
)
