import time
from importlib import metadata
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from buildbot.log import configure_logging
from buildbot.web.api.router import api_router
from buildbot.web.lifespan import lifespan_setup

APP_ROOT = Path(__file__).parent.parent


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url.path}")
        start_time = time.time()

        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - {round(duration, 3)}s"
        )

        return response


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    configure_logging()
    app = FastAPI(
        title="buildbot",
        version=metadata.version("buildbot"),
        lifespan=lifespan_setup,
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )

    app.add_middleware(RequestLoggingMiddleware)
    # Main router for the API.
    app.include_router(router=api_router, prefix="/api")
    # Adds static directory.
    # This directory is used to access swagger files.
    app.mount("/static", StaticFiles(directory=APP_ROOT / "static"), name="static")

    return app
