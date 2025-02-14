import enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class RedisSettings(BaseSettings):
    """Redis settings."""

    host: str = "redis://localhost"
    port: int = 6379

    def get_url(self) -> str:
        return f"redis://{self.host}:{self.port}/0"


class BuildBotJobSettings(BaseSettings):
    """BuildBotJob settings."""

    base_output_path: Path = "/var/lib/app/jobs/output"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BUILDBOT_",
        env_file_encoding="utf-8",
    )

    redis: RedisSettings = RedisSettings()
    buildbot_job: BuildBotJobSettings = BuildBotJobSettings()


settings = Settings()
