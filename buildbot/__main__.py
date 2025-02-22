import uvicorn
from app.core.settings import settings


def main() -> None:
    """Entrypoint of the application."""

    uvicorn.run(
        "app.api.application:get_app",
        workers=settings.uvicorn_workers_count,
        host=settings.host,
        port=settings.port,
        reload=settings.uvicorn_reload,
        log_level=settings.log_level.value.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
