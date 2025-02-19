import tarfile
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Generator, Union

import aiofiles
from app.core.settings import settings
from app.core.utils import AbstractSingletonMeta
from loguru import logger


class StorageService(ABC):
    """Interface for Object Storage Services such as S3, Azure Blob Storage, etc."""

    @abstractmethod
    async def upload(
        self,
        file_path: str,
        stream: Union[bytes, BytesIO, Generator[bytes, None, None]],
    ) -> str:
        """Uploads a file to the storage service."""

    @abstractmethod
    async def download(self, job_id: str, file_path: Path) -> BytesIO:
        """Downloads a file from the storage service."""

    @abstractmethod
    async def exists(self, job_id: str, file_path: Path) -> None:
        """Checks if a file exists in the storage service."""


class LocalStorageService(StorageService, metaclass=AbstractSingletonMeta):
    """A local file storage service."""

    def __init__(self) -> None:
        self._logger = logger
        self._volume = settings.local_storage.volume_path

    async def upload(
        self,
        file_path: Path,
        stream: Union[bytes, BytesIO, Generator[bytes, None, None]],
    ) -> str:
        """Uploads a file to the local storage, supporting bytes, BytesIO, and generators of bytes."""
        try:
            full_path = self._volume / file_path
            self._logger.info(f"Uploading '{full_path}' to local storage.")
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "wb") as f:
                if isinstance(stream, bytes):
                    await f.write(stream)
                elif isinstance(stream, BytesIO):
                    while chunk := stream.read(4096):
                        await f.write(chunk)
                else:
                    for chunk in stream:
                        await f.write(chunk)

            self._logger.info(f"File '{file_path}' uploaded to local storage.")
            return str(full_path)

        except Exception as e:
            self._logger.error(f"Error uploading file: {e}", exc_info=True)
            raise e

    async def download(self, job_id: str, file_path: Path) -> BytesIO:
        """Downloads a file from the local storage."""
        self._raise_if_not_exists(file_path)
        async with aiofiles.open(file_path, "rb") as f:
            return BytesIO(await f.read())

    def exists(self, file_path: Path) -> None:
        """Checks if a file exists in the local storage."""
        return (self._volume / file_path).exists()

    def _raise_if_not_exists(self, file_path: Path) -> None:
        if not self.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")


class TarStorageService(LocalStorageService):
    """A service for handling tar.gz files specifically."""

    def download(self, job_id: str, file_path: Path) -> BytesIO:
        """Checks if a file exists within the artifact path and returns its content as a BytesIO stream."""
        artifact_path = self._volume / job_id / "artifact.tar.gz"
        self._raise_if_not_exists(Path(job_id))
        with Path.open(artifact_path, "rb") as f:
            tar_buffer = BytesIO(f.read())
        with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.name.startswith(settings.job_manager.workdir):
                    member.name = member.name[len(settings.job_manager.workdir) :]
                if member.name == str(file_path):
                    file_content = tar.extractfile(member).read()
                    return BytesIO(file_content)
        raise FileNotFoundError(f"File {file_path} not found.")


def get_storage_service() -> StorageService:
    """Returns the storage service."""
    return TarStorageService()
