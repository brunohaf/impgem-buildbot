from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.background.broker import broker
from fastapi import FastAPI


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None, None]:  # pragma: no cover
    """
    Actions to run on application startup.

    This function uses fastAPI app to store data
    in the state, such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    app.middleware_stack = None
    if not broker.is_worker_process:
        await broker.startup()
    app.middleware_stack = app.build_middleware_stack()

    yield
    if not broker.is_worker_process:
        await broker.shutdown()
