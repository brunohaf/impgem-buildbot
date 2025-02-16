import taskiq_fastapi
from taskiq import AsyncBroker, InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

broker: AsyncBroker = InMemoryBroker()
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
taskiq_fastapi.init(
    broker,
    "app.api.application:get_app",
)
