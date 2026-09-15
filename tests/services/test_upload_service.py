from unittest.mock import Mock

from app.services.upload_service import UploadService


def test_upload_saves_the_content_and_persists_metadata() -> None:
    storage = Mock()
    storage.save.return_value = "/storage/uploads/some-path"
    file_repository = Mock()
    service = UploadService(storage=storage, file_repository=file_repository)

    service.upload(
        user_id="user-1",
        filename="report.pdf",
        file_type="application/pdf",
        content=b"file-bytes",
    )

    saved_file_id, saved_content = storage.save.call_args.args
    assert saved_content == b"file-bytes"

    file_repository.create.assert_called_once_with(
        file_id=saved_file_id,
        user_id="user-1",
        filename="report.pdf",
        file_type="application/pdf",
        byte_length=len(b"file-bytes"),
        storage_path="/storage/uploads/some-path",
    )


def test_upload_returns_the_persisted_metadata_record() -> None:
    storage = Mock()
    file_repository = Mock()
    expected_record = Mock()
    file_repository.create.return_value = expected_record
    service = UploadService(storage=storage, file_repository=file_repository)

    result = service.upload(
        user_id="user-1", filename="a.txt", file_type="text/plain", content=b"x"
    )

    assert result is expected_record
