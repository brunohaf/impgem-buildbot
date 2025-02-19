from io import BytesIO
from typing import Any, Generator, Optional, Union


class JobOutput:
    """Class for job output."""

    stderr: BytesIO
    stdout: BytesIO

    def __init__(
        self,
        job_id: str,
        stderr: Optional[Union[bytes, Generator[bytes, Any, None]]] = None,
        stdout: Optional[Union[bytes, Generator[bytes, Any, None]]] = None,
    ) -> None:
        self.job_id = job_id
        self.stderr = self._to_bytesio(stderr)
        self.stdout = self._to_bytesio(stdout)

    def _to_bytesio(
        self,
        output: Optional[Union[bytes, Generator[bytes, Any, None]]],
    ) -> BytesIO:
        """Converts bytes or a generator of bytes into a BytesIO stream."""
        buffer = BytesIO()
        if output is None:
            return buffer
        if isinstance(output, bytes):
            buffer.write(output)
        elif isinstance(output, Generator):
            for chunk in output:
                buffer.write(chunk)
        buffer.seek(0)
        return buffer
