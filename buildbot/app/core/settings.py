import enum
from pathlib import Path

from app.core.enums import JobArtifactStorage
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

    host: str = "localhost"
    port: int = 6379

    def get_url(self) -> str:
        """Returns a Redis URL."""
        return f"redis://{self.host}:{self.port}/0"


class JobManagerSettings(BaseSettings):
    """BuildBotJob settings."""

    """Job Base Workdir"""
    workdir: Path = "/workdir"

    """Job Handler Schedule"""
    handler_schedule: str = "*/3 * * * *"

    """Job Maximum Time to Live in Seconds"""
    job_ttl: int = 300

    """Job Artifact Storage"""
    artifact_storage: JobArtifactStorage = JobArtifactStorage.TAR_GZ

    """Concurrent Jobs"""
    concurrent_jobs: int = 10

    """Job Artifact Path Templates"""
    artifact_path_template: str = "{job_id}/artifact_{filename}"
    log_path_template: str = "{job_id}/logs/{filename}"


class LocalStorageSettings(BaseSettings):
    """LocalStorage settings."""

    volume_path: Path = (Path.cwd() / "data").resolve()


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

    log_level: LogLevel = LogLevel.DEBUG

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BUILDBOT_",
        env_file_encoding="utf-8",
    )

    redis: RedisSettings = RedisSettings()
    job_manager: JobManagerSettings = JobManagerSettings()
    local_storage: LocalStorageSettings = LocalStorageSettings()


settings = Settings()
