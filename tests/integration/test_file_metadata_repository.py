import uuid

import pytest
from sqlalchemy.orm import Session

from app.repositories import FileMetadataRepository

pytestmark = pytest.mark.integration


def test_create_persists_and_returns_the_record(db_session: Session) -> None:
    repository = FileMetadataRepository(db_session)
    file_id = uuid.uuid4()

    record = repository.create(
        file_id=file_id,
        user_id="user-1",
        filename="report.pdf",
        file_type="application/pdf",
        byte_length=1234,
        storage_path="/storage/uploads/report.pdf",
    )

    assert record.file_id == file_id
    assert record.uploaded_at is not None


def test_get_returns_a_previously_created_record(db_session: Session) -> None:
    repository = FileMetadataRepository(db_session)
    file_id = uuid.uuid4()
    repository.create(
        file_id=file_id,
        user_id="user-1",
        filename="report.pdf",
        file_type="application/pdf",
        byte_length=1234,
        storage_path="/storage/uploads/report.pdf",
    )

    fetched = repository.get(file_id)

    assert fetched is not None
    assert fetched.filename == "report.pdf"
    assert fetched.user_id == "user-1"


def test_get_returns_none_for_an_unknown_file_id(db_session: Session) -> None:
    repository = FileMetadataRepository(db_session)

    assert repository.get(uuid.uuid4()) is None
