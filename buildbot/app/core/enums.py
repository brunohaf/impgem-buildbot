from enum import StrEnum, auto


class JobArtifactStorage(StrEnum):
    """Enum for Job Artifact Storage types."""

    LOCAL = auto()
    TAR_GZ = auto()
