import uuid
from pathlib import Path


class FileStorage:
    """Writes uploaded file contents to a non-public directory on the local filesystem."""

    # Stores the storage directory and ensures it exists on disk.
    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = storage_dir
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    # Writes the file's bytes to disk and returns the resulting path.
    def save(self, file_id: uuid.UUID, content: bytes) -> str:
        path = self._storage_dir / str(file_id)
        path.write_bytes(content)
        return str(path)
