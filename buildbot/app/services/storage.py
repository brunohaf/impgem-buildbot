import tarfile
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path
from typing import Generator, Union

import aiofiles
from app.core.settings import JobManagerSettings, settings
from app.core.utils import AbstractSingletonMeta
from loguru import logger

_CHUNK_SIZE = 1024 * 1024
_job_manager_settings: JobManagerSettings = settings.job_manager_settings
_artifact_path_template: str = _job_manager_settings.artifact_path_template


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
    async def download(
        self,
        job_id: str,
        file_path: Path,
    ) -> Union[bytes, BytesIO, Generator[bytes, None, None]]:
        """
        Downloads a file as a .tar.gz from the storage service..

        :param job_id: The job ID.
        :param file_path: The path to the file.
        :return: A BytesIO object containing the file content.
        :raises FileNotFoundError: If the file is not found.
        """

    @abstractmethod
    async def exists(self, job_id: str, file_path: Path) -> bool:
        """Checks if a file exists in the storage service."""


class LocalStorageService(StorageService, metaclass=AbstractSingletonMeta):
    """A service for handling local tar.gz artifacts."""

    def __init__(self) -> None:
        self._logger = logger
        self._volume = settings.artifact_storage_settings.volume_path.resolve()

    async def upload(
        self,
        file_path: Path,
        stream: Union[bytes, BytesIO, Generator[bytes, None, None]],
    ) -> str:
        """Uploads a file to the local storage, supporting bytes, BytesIO, and generators of bytes."""
        try:
            full_path = self._volume / file_path
            self._logger.debug(
                f"file_path='{file_path}', self._volume='{self._volume}'",
            )
            self._logger.info(f"Uploading '{full_path}' to local storage.")

            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "wb") as f:
                if isinstance(stream, bytes):
                    await f.write(stream)
                elif isinstance(stream, BytesIO):
                    while chunk := stream.read(_CHUNK_SIZE):
                        await f.write(chunk)
                else:
                    for chunk in stream:
                        await f.write(chunk)

            self._logger.info(f"File '{file_path}' uploaded to local storage.")
            return str(full_path)

        except Exception as e:
            self._logger.error(f"Error uploading file: {e}", exc_info=True)
            raise e

    def exists(self, file_path: Path) -> bool:
        """Checks if a file exists in the local storage."""
        return (self._volume / file_path).exists()

    def download(
        self,
        job_id: str,
        file_path: Path,
    ) -> BytesIO:
        """
        Downloads a file from the local storage.

        :param job_id: The job ID.
        :param file_path: The path to the file.
        :return: A BytesIO object containing the file content.
        :raises FileNotFoundError: If the file is not found.
        """
        artifact_path = _artifact_path_template.format(job_id=job_id)

        workdir = Path(_job_manager_settings.workdir)
        workdir = workdir.relative_to("/") if workdir.is_absolute() else workdir

        self._raise_if_not_exists(Path(job_id))

        with tarfile.open(self._volume / artifact_path, mode="r:*") as tar:
            for member in tar.getmembers():
                member_path = Path(member.path).relative_to(workdir)
                if member_path == file_path:
                    return self._get_tar_stream(
                        tar.extractfile(member).read(),
                        member_path.name,
                    )

        raise FileNotFoundError(f"File {file_path} not found.")

    def _raise_if_not_exists(self, file_path: Path) -> None:
        if not self.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

    def _get_tar_stream(self, file_content: bytes, filename: str) -> BytesIO:
        tar_stream = BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w:gz") as tar:
            tar_info = tarfile.TarInfo(name=filename)
            tar_info.size = len(file_content)
            tar.addfile(tar_info, BytesIO(file_content))
        tar_stream.seek(0)
        return tar_stream


def get_storage_service() -> StorageService:
    """Returns the storage service."""
    return LocalStorageService()
