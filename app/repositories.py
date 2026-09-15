import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, FileMetadata, SignedURLMapping


class FileMetadataRepository:
    # Stores the DB session used for all queries on this repository.
    def __init__(self, db: Session) -> None:
        self._db = db

    # Inserts a new file metadata record and returns the persisted row.
    def create(
        self,
        *,
        file_id: uuid.UUID,
        user_id: str,
        filename: str,
        file_type: str,
        byte_length: int,
        storage_path: str,
    ) -> FileMetadata:
        record = FileMetadata(
            file_id=file_id,
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            byte_length=byte_length,
            storage_path=storage_path,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    # Fetches a file metadata record by its ID, or None if it doesn't exist.
    def get(self, file_id: uuid.UUID) -> FileMetadata | None:
        return self._db.get(FileMetadata, file_id)


class SignedURLRepository:
    # Stores the DB session used for all queries on this repository.
    def __init__(self, db: Session) -> None:
        self._db = db

    # Inserts a new signed URL mapping and returns the persisted row.
    def create(
        self,
        *,
        file_id: uuid.UUID,
        signed_url: str,
        ttl_seconds: int,
        expires_at: datetime,
    ) -> SignedURLMapping:
        record = SignedURLMapping(
            id=uuid.uuid4(),
            file_id=file_id,
            signed_url=signed_url,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    # Returns the most recently issued, still-unexpired signed URL for a file, if any.
    def get_active(self, file_id: uuid.UUID) -> SignedURLMapping | None:
        stmt = (
            select(SignedURLMapping)
            .where(
                SignedURLMapping.file_id == file_id,
                SignedURLMapping.expires_at > datetime.now(timezone.utc),
            )
            .order_by(SignedURLMapping.issued_at.desc())
        )
        return self._db.scalars(stmt).first()


class AuditEventRepository:
    # Stores the DB session used for all queries on this repository.
    def __init__(self, db: Session) -> None:
        self._db = db

    # Records an audit event for a signed URL being issued.
    def record_signed_url_issued(
        self,
        *,
        file_id: uuid.UUID,
        requested_by: str,
        expires_at: datetime,
    ) -> AuditEvent:
        event = AuditEvent(
            id=uuid.uuid4(),
            file_id=file_id,
            requested_by=requested_by,
            expires_at=expires_at,
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event
