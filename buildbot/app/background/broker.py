import taskiq_fastapi
from app.background.job_manager import RunnerJob, run
from taskiq import AsyncBroker, InMemoryBroker

broker: AsyncBroker = InMemoryBroker()


@broker.task
async def job_runner_task(runner_job: RunnerJob):
    """
    Taskiq worker task to run the bash script.
    """
    await run(runner_job)


taskiq_fastapi.init(
    broker,
    "app.web.application:get_app",
)
