from enum import StrEnum


class JobManagerType(StrEnum):
    """Job manager type."""

    BASE = "base"
    CONTAINER = "container"


class Environment(StrEnum):
    """BuildBot environment."""

    PROD = "production"
    DEV = "development"
