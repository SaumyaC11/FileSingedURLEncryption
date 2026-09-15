from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.repositories import AuditEventRepository, FileMetadataRepository, SignedURLRepository
from app.services.file_retrieval_service import FileRetrievalService
from app.services.file_storage import FileStorage
from app.services.signed_url_service import SignedURLService
from app.services.signed_url_signer import SignedURLSigner
from app.services.status_service import StatusService
from app.services.upload_service import UploadService

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


# Builds an UploadService wired to file storage and the file metadata repository.
def get_upload_service(db: DbSession, settings: AppSettings) -> UploadService:
    return UploadService(
        storage=FileStorage(settings.storage_dir),
        file_repository=FileMetadataRepository(db),
    )


# Builds a SignedURLService wired to the signer, repositories, and base URL.
def get_signed_url_service(db: DbSession, settings: AppSettings) -> SignedURLService:
    return SignedURLService(
        signer=SignedURLSigner(settings.signed_url_secret_key, settings.signed_url_salt),
        file_repository=FileMetadataRepository(db),
        signed_url_repository=SignedURLRepository(db),
        audit_repository=AuditEventRepository(db),
        base_url=settings.base_url,
    )


# Builds a StatusService wired to the file and signed URL repositories.
def get_status_service(db: DbSession) -> StatusService:
    return StatusService(
        file_repository=FileMetadataRepository(db),
        signed_url_repository=SignedURLRepository(db),
    )


# Builds a FileRetrievalService wired to the signer and file metadata repository.
def get_file_retrieval_service(db: DbSession, settings: AppSettings) -> FileRetrievalService:
    return FileRetrievalService(
        signer=SignedURLSigner(settings.signed_url_secret_key, settings.signed_url_salt),
        file_repository=FileMetadataRepository(db),
    )
