import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker, ZeroMQBroker

from buildbot.settings import settings

broker: AsyncBroker = ZeroMQBroker()

if settings.environment.lower() == "pytest":
    broker = InMemoryBroker()

taskiq_fastapi.init(
    broker,
    "buildbot.web.application:get_app",
)
