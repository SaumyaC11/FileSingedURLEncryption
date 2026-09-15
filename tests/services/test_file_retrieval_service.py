import uuid
from unittest.mock import Mock

import pytest

from app.services.file_retrieval_service import FileNotFoundError, FileRetrievalService


@pytest.fixture
def signer() -> Mock:
    return Mock()


@pytest.fixture
def file_repository() -> Mock:
    return Mock()


@pytest.fixture
def service(signer: Mock, file_repository: Mock) -> FileRetrievalService:
    return FileRetrievalService(signer=signer, file_repository=file_repository)


def test_resolve_returns_the_metadata_for_a_valid_token(
    service: FileRetrievalService, signer: Mock, file_repository: Mock
) -> None:
    file_id = uuid.uuid4()
    signer.unsign.return_value = file_id
    expected_metadata = Mock()
    file_repository.get.return_value = expected_metadata

    result = service.resolve("some-token")

    signer.unsign.assert_called_once_with("some-token")
    assert result is expected_metadata


def test_resolve_raises_when_the_file_no_longer_exists(
    service: FileRetrievalService, signer: Mock, file_repository: Mock
) -> None:
    signer.unsign.return_value = uuid.uuid4()
    file_repository.get.return_value = None

    with pytest.raises(FileNotFoundError):
        service.resolve("some-token")


def test_resolve_propagates_signer_errors(
    service: FileRetrievalService, signer: Mock
) -> None:
    class BoomError(Exception):
        pass

    signer.unsign.side_effect = BoomError("invalid")

    with pytest.raises(BoomError):
        service.resolve("bad-token")
