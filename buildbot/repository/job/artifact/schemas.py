from io import BytesIO
from pathlib import Path

from buildbot.core.settings import settings
from buildbot.repository.schemas import RepositoryBaseModel


class JobArtifact(RepositoryBaseModel):
    """Simple JobArtifact model."""

    job_id: str
    content: BytesIO

    @property
    def output_path(self) -> Path:
        return settings.ARTIFACTS_PATH / self.job_id
