from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.background.broker import broker
from fastapi import FastAPI


@asynccontextmanager
async def lifespan_setup(
    app: FastAPI,
) -> AsyncGenerator[None, None]:  # pragma: no cover
    """
    Actions to run on application startup and shutdown.

    This function initializes required services on startup
    and ensures cleanup on shutdown.

    :param app: the FastAPI application.
    :return: Async generator for the app lifespan.
    """

    app.middleware_stack = None
    try:
        if not broker.is_worker_process:
            await broker.startup()
        app.middleware_stack = app.build_middleware_stack()

        yield

    finally:
        if not broker.is_worker_process:
            await broker.shutdown()
