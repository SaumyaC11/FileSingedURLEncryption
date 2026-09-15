import uuid
from datetime import datetime, timedelta, timezone

from app.repositories import AuditEventRepository, FileMetadataRepository, SignedURLRepository
from app.services.signed_url_signer import SignedURLSigner


class FileNotFoundError(Exception):
    """Raised when generating a signed URL for a file that does not exist."""


class SignedURLResult:
    def __init__(self, signed_url: str, expires_at: datetime) -> None:
        self.signed_url = signed_url
        self.expires_at = expires_at


class SignedURLService:
    """Orchestrates issuing a signed, time-limited URL for a stored file."""

    def __init__(
        self,
        signer: SignedURLSigner,
        file_repository: FileMetadataRepository,
        signed_url_repository: SignedURLRepository,
        audit_repository: AuditEventRepository,
        base_url: str,
    ) -> None:
        self._signer = signer
        self._file_repository = file_repository
        self._signed_url_repository = signed_url_repository
        self._audit_repository = audit_repository
        self._base_url = base_url.rstrip("/")

    def generate(
        self,
        *,
        file_id: uuid.UUID,
        ttl_seconds: int,
        requesting_user_id: str,
    ) -> SignedURLResult:
        if self._file_repository.get(file_id) is None:
            raise FileNotFoundError(f"File {file_id} does not exist")

        token = self._signer.sign(file_id)
        signed_url = f"{self._base_url}/v1/returnFile?token={token}"
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        self._signed_url_repository.create(
            file_id=file_id,
            signed_url=signed_url,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
        )
        self._audit_repository.record_signed_url_issued(
            file_id=file_id,
            requested_by=requesting_user_id,
            expires_at=expires_at,
        )

        return SignedURLResult(signed_url=signed_url, expires_at=expires_at)
