from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

from buildbot.core.enums import DataContext
from buildbot.core.utils import SingletonMeta
from buildbot.data.schemas import StorageBaseModel


class Storage(ABC):
    """Interface for storage classes."""

    @abstractmethod
    def add(self, data: StorageBaseModel) -> None:
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[StorageBaseModel]:
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, StorageBaseModel]:
        pass

    @abstractmethod
    def update(self, new_data: StorageBaseModel) -> Optional[StorageBaseModel]:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class InMemoryStorage(Storage, metaclass=SingletonMeta):
    """Handles in-memory storage, ensuring singleton per data context."""

    def __init__(self, data_context: DataContext):
        self._storage: Dict[str, StorageBaseModel] = {}
        self._logger = logger
        self._data_context = data_context

    def add(self, entity: StorageBaseModel) -> None:
        """Add an entity to the storage."""
        self._storage[entity.id] = entity

    def get(self, id: str) -> Optional[StorageBaseModel]:
        """Retrieve an entity by its ID."""
        return self._storage.get(id)

    def update(
        self, new_data: StorageBaseModel
    ) -> Optional[StorageBaseModel]:
        """Updates existing data."""

        if self._storage.get(new_data.id) is None:
            self._logger.info(
                f"Failed to update {self._data_context}(id={new_data.id}) "
                f"because it doesn't exist"
            )
            return

        self._storage[id] = new_data
        self._logger.info(f"Successfully updated entity with ID: {id}")

        return new_data


class InMemoryTaskStorage(InMemoryStorage):
    """Singleton storage for tasks."""


class InMemoryJobStorage(InMemoryStorage):
    """Singleton storage for jobs."""


def get_storage(data_context: DataContext) -> InMemoryStorage:
    return InMemoryStorage(data_context)
