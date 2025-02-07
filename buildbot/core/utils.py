import os
import shutil
from io import BytesIO
from pathlib import Path

import aiofiles


class SingletonMeta(type):
    """Metaclass for enforcing the Singleton pattern."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


async def zip_folder(folder_path: Path) -> BytesIO:
    """Zip the entire folder using shutil and return as a BytesIO stream."""
    zip_buffer = BytesIO()

    temp_zip_path = folder_path.parent / f"{folder_path.name}.zip"

    shutil.make_archive(temp_zip_path.stem, "zip", folder_path)

    async with aiofiles.open(temp_zip_path, "rb") as f:
        content = await f.read()
        zip_buffer.write(content)

    os.remove(temp_zip_path)

    zip_buffer.seek(0)
    return zip_buffer
