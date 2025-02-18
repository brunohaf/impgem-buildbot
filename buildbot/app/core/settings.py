import enum
from datetime import datetime, timezone
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


class ContainerJobManagerSettings(BaseSettings):
    """Container Job Manager settings."""

    """Docker Client Host"""
    host: str = "localhost"

    """Docker Client Port"""
    port: int = 2375

    """Docker Image Tag"""
    tag: str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    @property
    def command_template(self) -> str:
        """Returns a Docker command template."""
        return (
            '"cat <<EOF > run.sh'
            "\n{script}"
            "\nEOF"
            "\nchmod +x run.sh"
            "\ntimeout {timeout}s"
            ' ./run.sh && rm run.sh"'
        )

    @property
    def config(self) -> dict:
        """Returns a Docker container configuration."""
        return {
            "network_mode": "none",
            "detach": True,
            "cap_drop": ["ALL"],
            "security_opt": ["no-new-privileges"],
            "stderr": True,
            "stdout": True,
        }

    @property
    def image_config(self) -> dict:
        """Returns a Docker image configuration."""
        dockerfile = (
            Path.cwd() / "buildbot" / "app" / "background" / "job_manager" / "container"
        )
        return {
            "tag": f"buildbot/runner:{self.tag}",
            "path": str(dockerfile),
        }


class JobManagerSettings(BaseSettings):
    """BuildBotJob settings."""

    """Job Base Workdir"""
    workdir: Path = "/workdir"

    """Job Manager Schedule"""
    manager_schedule: str = "*/3 * * * *"

    """Job Maximum Time to Live in Seconds"""
    job_ttl: int = 300

    """Job Artifact Storage"""
    artifact_storage: JobArtifactStorage = JobArtifactStorage.TAR_GZ

    """Concurrent Jobs"""
    concurrent_jobs: int = 10

    """Job Artifact Path Templates"""
    artifact_path_template: str = "{job_id}/artifact_{filename}"
    log_path_template: str = "{job_id}/logs/{filename}"

    container: ContainerJobManagerSettings = ContainerJobManagerSettings()


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
