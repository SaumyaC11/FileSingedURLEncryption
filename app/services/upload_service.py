import uuid

from app.models import FileMetadata
from app.repositories import FileMetadataRepository
from app.services.file_storage import FileStorage


class UploadService:
    """Orchestrates persisting an uploaded file's bytes and its metadata."""

    # Stores the file storage and metadata repository used during upload.
    def __init__(self, storage: FileStorage, file_repository: FileMetadataRepository) -> None:
        self._storage = storage
        self._file_repository = file_repository

    # Saves the file's bytes to storage and persists its metadata record.
    def upload(
        self,
        *,
        user_id: str,
        filename: str,
        file_type: str,
        content: bytes,
    ) -> FileMetadata:
        file_id = uuid.uuid4()
        storage_path = self._storage.save(file_id, content)
        return self._file_repository.create(
            file_id=file_id,
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            byte_length=len(content),
            storage_path=storage_path,
        )
