import uuid
from pathlib import Path

from app.services.file_storage import FileStorage


def test_save_creates_the_storage_directory_if_missing(tmp_path: Path) -> None:
    storage_dir = tmp_path / "uploads"

    FileStorage(storage_dir)

    assert storage_dir.is_dir()


def test_save_writes_the_content_and_returns_its_path(tmp_path: Path) -> None:
    storage = FileStorage(tmp_path)
    file_id = uuid.uuid4()

    path = storage.save(file_id, b"hello world")

    assert Path(path) == tmp_path / str(file_id)
    assert Path(path).read_bytes() == b"hello world"
