from pathlib import Path

import aiofiles


async def get_file_by_path(path: Path) -> bytes:
    """
    Reads a file by its path asynchronously.

    Args:
        path (Path): Path to the file.

    Returns:
        bytes: The content of the file.

    Raises:
        FileNotFoundError: If the file was not found.
    """
    try:
        await path.stat()
    except FileNotFoundError:
        raise
    async with aiofiles.open(path, "rb") as f:
        return await f.read()
