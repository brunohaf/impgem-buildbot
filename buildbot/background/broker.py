from pathlib import Path
from typing import Dict

import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker

from buildbot.background.job_runner import RunnerJob, run

broker: AsyncBroker = InMemoryBroker()


@broker.task
async def job_runner_task(runner_job: RunnerJob):
    """
    Taskiq worker task to run the bash script.
    """
    await run(runner_job)


taskiq_fastapi.init(
    broker,
    "buildbot.web.application:get_app",
)
