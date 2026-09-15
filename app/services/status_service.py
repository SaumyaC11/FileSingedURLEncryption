import uuid

from app.models import FileMetadata
from app.repositories import FileMetadataRepository, SignedURLRepository


class FileNotFoundError(Exception):
    """Raised when querying status for a file that does not exist."""


class NotFileOwnerError(Exception):
    """Raised when a non-owner queries a file's status."""


class FileStatus:
    # Extracts the display fields for a file's status from its metadata.
    def __init__(self, metadata: FileMetadata, signed_url: str | None) -> None:
        self.filename = metadata.filename
        self.byte_length = metadata.byte_length
        self.uploaded_at = metadata.uploaded_at
        self.signed_url = signed_url


class StatusService:
    """Looks up a file's metadata and its currently active signed URL, if any."""

    # Stores the file and signed URL repositories used to look up status.
    def __init__(
        self,
        file_repository: FileMetadataRepository,
        signed_url_repository: SignedURLRepository,
    ) -> None:
        self._file_repository = file_repository
        self._signed_url_repository = signed_url_repository

    # Validates ownership and returns the file's metadata plus its active signed URL.
    def get_status(self, *, file_id: uuid.UUID, requesting_user_id: str) -> FileStatus:
        metadata = self._file_repository.get(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File {file_id} does not exist")
        if metadata.user_id != requesting_user_id:
            raise NotFileOwnerError(f"User {requesting_user_id} does not own file {file_id}")

        active_mapping = self._signed_url_repository.get_active(file_id)
        return FileStatus(
            metadata=metadata,
            signed_url=active_mapping.signed_url if active_mapping else None,
        )
