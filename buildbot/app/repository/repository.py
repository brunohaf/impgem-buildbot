from abc import ABC, abstractmethod
from typing import Optional

from app.core.utils import AbstractSingletonMeta
from app.repository.schemas import RepositoryBaseModel
from loguru import logger
from redis import asyncio as aioredis


# ? Although there is a Logging Middleware in FastAPI,
# ? A logging Decorator method or class could improve observability while
# ? avoiding to clutter the code with verbose logging code.
class BaseRepository(ABC):
    """Interface for RepositoryBaseModel's repository implementation classes."""

    @abstractmethod
    async def create(self, model: RepositoryBaseModel) -> None:
        """Creates a new model in the repository."""

    @abstractmethod
    async def get(self, id: str) -> Optional[RepositoryBaseModel]:
        """Retrieves a model by ID."""

    @abstractmethod
    async def update(self, model: RepositoryBaseModel) -> None:
        """Updates a model in the repository."""

    @abstractmethod
    async def delete(self, id: str) -> None:
        """Deletes a model by ID."""


# ? This is a Redis-based implementation of the RepositoryBaseModel class.
# ? It uses connection pooling and Singleton pattern for connection management.


class BaseRedisRepository(BaseRepository, metaclass=AbstractSingletonMeta):
    """Redis-backed Repository using connection pooling and Singleton."""

    _pool = None

    @classmethod
    def initialize(
        cls,
        redis_url: str = "redis://localhost:6379/0",
    ) -> "BaseRedisRepository":
        """Initializes the connection pool."""
        if cls._pool is None:
            cls._pool = aioredis.ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
            )
        return cls(cls._pool)

    def __init__(self, pool: aioredis.ConnectionPool) -> None:
        self._redis = aioredis.Redis(connection_pool=pool)
        self._logger = logger

    @abstractmethod
    def _get_key(self, id: str) -> str:
        pass
