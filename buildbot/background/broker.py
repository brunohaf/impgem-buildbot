import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker

broker: AsyncBroker = InMemoryBroker()

taskiq_fastapi.init(
    broker,
    "buildbot.web.application:get_app",
)
