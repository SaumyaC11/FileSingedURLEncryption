import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.repositories import AuditEventRepository, FileMetadataRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def existing_file_id(db_session: Session) -> uuid.UUID:
    file_id = uuid.uuid4()
    FileMetadataRepository(db_session).create(
        file_id=file_id,
        user_id="user-1",
        filename="report.pdf",
        file_type="application/pdf",
        byte_length=1234,
        storage_path="/storage/uploads/report.pdf",
    )
    return file_id


def test_record_signed_url_issued_persists_the_audit_event(
    db_session: Session, existing_file_id: uuid.UUID
) -> None:
    repository = AuditEventRepository(db_session)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    event = repository.record_signed_url_issued(
        file_id=existing_file_id, requested_by="user-1", expires_at=expires_at
    )

    assert event.id is not None
    assert event.file_id == existing_file_id
    assert event.requested_by == "user-1"
