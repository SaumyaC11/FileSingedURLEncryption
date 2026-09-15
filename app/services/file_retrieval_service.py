from app.models import FileMetadata
from app.repositories import FileMetadataRepository
from app.services.signed_url_signer import ExpiredSignedToken, InvalidSignedToken, SignedURLSigner

__all__ = ["ExpiredSignedToken", "InvalidSignedToken", "FileNotFoundError", "FileRetrievalService"]


class FileNotFoundError(Exception):
    """Raised when a validly signed token points at a file that no longer exists."""


class FileRetrievalService:
    """Validates a signed token and resolves it to the stored file to serve."""

    # Stores the signer and file repository used to resolve tokens.
    def __init__(self, signer: SignedURLSigner, file_repository: FileMetadataRepository) -> None:
        self._signer = signer
        self._file_repository = file_repository

    # Verifies the token and returns the file metadata it refers to.
    def resolve(self, token: str) -> FileMetadata:
        file_id = self._signer.unsign(token)
        metadata = self._file_repository.get(file_id)
        if metadata is None:
            raise FileNotFoundError(f"File {file_id} does not exist")
        return metadata
