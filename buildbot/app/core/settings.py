import base64
import enum
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Union

from app.core.enums import Environment, JobManagerType
from pydantic import BaseModel, Discriminator, Tag
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class RedisSettings(BaseModel):
    """Redis settings."""

    host: str = "localhost"
    port: int = 6379

    def get_url(self) -> str:
        """Returns a Redis URL."""
        return f"redis://{self.host}:{self.port}/0"


class JobManagerSettings(BaseModel):
    """BuildBotJob settings."""

    type: JobManagerType = JobManagerType.BASE

    workdir: str = "workdir"
    """Job Base Workdir"""

    schedule: str = "*/1 * * * *"
    """Job Manager Schedule"""

    job_timeout: int = 300
    """Job Maximum Time to Live in Seconds"""

    concurrent_jobs: int = 10
    """Concurrent Jobs"""

    artifact_path_template: str = "{job_id}/artifact.tar.gz"
    """Job Artifact Path Templates"""

    log_path_template: str = "{job_id}/logs.tar.gz"
    """Job Logs Path Templates"""

    @staticmethod
    def discriminator(v: Any) -> JobManagerType:
        """Discriminator for job_manager_settings."""
        if isinstance(v, dict):
            return v.get("type")
        if isinstance(v, JobManagerSettings):
            return v.type
        return None


class ContainerJobManagerSettings(JobManagerSettings):
    """Container Job Manager settings."""

    # ? Docker Image Tag
    image_tag: str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # ? Dockerfile Directory Path
    dockerfile_path: Path = Path("buildbot/app/background/job_manager/container")

    # ? Script Path
    _script_path: str = "run.sh"

    # ? Docker Container Configuration
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

    # ? Docker Image Configuration
    @property
    def image_config(self) -> dict:
        """Returns a Docker image configuration."""
        _workdir = Path(f"/{self.workdir}")
        return {
            "tag": self.image_tag,
            "path": str(self.dockerfile_path),
            "buildargs": {
                "WORKDIR": str(_workdir),
                "SCRIPT_PATH": f"{_workdir}/{self._script_path}",
            },
        }

    def get_command(self, script: str) -> str:
        """Generates a Docker command, encodes the script, sets a timeout and deletes run.sh."""
        encoded_script = base64.b64encode(script.encode()).decode()

        return (
            f'"echo {encoded_script} | base64 -d > {self._script_path} '
            f"&& chmod +x {self._script_path} && timeout {self.job_timeout}s "
            f'./{self._script_path}; rm -f {self._script_path}"'
        )


class ArtifactStorageSettings(BaseModel):
    """Job Artifact Storage settings."""

    volume_path: Path = Path("data")
    """Artifact Storage Volume Path"""


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000

    log_level: LogLevel = LogLevel.INFO

    # ? Quantity of workers for uvicorn
    uvicorn_workers_count: int = 1

    # ? Enable uvicorn reloading
    uvicorn_reload: bool = False

    # ? Current environment
    environment: Environment = Environment.PROD

    if environment == Environment.DEV:
        uvicorn_reload = True
        log_level = LogLevel.DEBUG

    # ? Redis
    redis_settings: RedisSettings

    # ? Job Manager
    job_manager_settings: Annotated[
        Union[
            Annotated[ContainerJobManagerSettings, Tag(JobManagerType.CONTAINER)],
            Annotated[JobManagerSettings, Tag(JobManagerType.BASE)],
        ],
        Discriminator(JobManagerSettings.discriminator),
    ]
    # ? Job Artifact Storage
    artifact_storage_settings: ArtifactStorageSettings

    # ? Pydantic Env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BUILDBOT_",
        env_file_encoding="utf-8",
        extra="allow",
        env_nested_delimiter="__",
    )


settings = Settings()
