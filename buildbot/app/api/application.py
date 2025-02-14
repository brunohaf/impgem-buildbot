import time
from importlib import metadata
from pathlib import Path

from app.api.lifespan import lifespan_setup
from app.api.router import api_router
from app.core.log import configure_logging
from fastapi import FastAPI, Request
from fastapi.responses import UJSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

APP_ROOT = Path(__file__).parent.parent


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each incoming request and outgoing response."""

    async def dispatch(self, request: Request, call_next: callable) -> None:
        """Logs the request method, path, response status code and duration of the request."""  # noqa: E501
        logger.info(f"Request: {request.method} {request.url.path}")
        start_time = time.time()

        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {round(duration, 3)}s")

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
