import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.repositories import FileMetadataRepository, SignedURLRepository

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


def test_get_active_returns_none_when_no_signed_url_exists(
    db_session: Session, existing_file_id: uuid.UUID
) -> None:
    repository = SignedURLRepository(db_session)

    assert repository.get_active(existing_file_id) is None


def test_get_active_returns_a_non_expired_signed_url(
    db_session: Session, existing_file_id: uuid.UUID
) -> None:
    repository = SignedURLRepository(db_session)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    created = repository.create(
        file_id=existing_file_id,
        signed_url="http://localhost:8000/v1/returnFile?token=abc",
        ttl_seconds=3600,
        expires_at=expires_at,
    )

    active = repository.get_active(existing_file_id)

    assert active is not None
    assert active.id == created.id


def test_get_active_ignores_an_expired_signed_url(
    db_session: Session, existing_file_id: uuid.UUID
) -> None:
    repository = SignedURLRepository(db_session)
    expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    repository.create(
        file_id=existing_file_id,
        signed_url="http://localhost:8000/v1/returnFile?token=expired",
        ttl_seconds=1,
        expires_at=expires_at,
    )

    assert repository.get_active(existing_file_id) is None


def test_get_active_returns_the_most_recently_issued_signed_url(
    db_session: Session, existing_file_id: uuid.UUID
) -> None:
    repository = SignedURLRepository(db_session)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    repository.create(
        file_id=existing_file_id,
        signed_url="http://localhost:8000/v1/returnFile?token=first",
        ttl_seconds=3600,
        expires_at=expires_at,
    )
    newest = repository.create(
        file_id=existing_file_id,
        signed_url="http://localhost:8000/v1/returnFile?token=second",
        ttl_seconds=3600,
        expires_at=expires_at,
    )

    active = repository.get_active(existing_file_id)

    assert active is not None
    assert active.id == newest.id
