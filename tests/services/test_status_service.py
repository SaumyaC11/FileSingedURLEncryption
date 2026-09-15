import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.services.status_service import FileNotFoundError, NotFileOwnerError, StatusService


@pytest.fixture
def file_repository() -> Mock:
    return Mock()


@pytest.fixture
def signed_url_repository() -> Mock:
    return Mock()


@pytest.fixture
def service(file_repository: Mock, signed_url_repository: Mock) -> StatusService:
    return StatusService(
        file_repository=file_repository, signed_url_repository=signed_url_repository
    )


def test_get_status_raises_when_the_file_does_not_exist(
    service: StatusService, file_repository: Mock
) -> None:
    file_repository.get.return_value = None

    with pytest.raises(FileNotFoundError):
        service.get_status(file_id=uuid.uuid4(), requesting_user_id="user-1")


def test_get_status_raises_when_the_requester_is_not_the_owner(
    service: StatusService, file_repository: Mock
) -> None:
    file_repository.get.return_value = Mock(user_id="owner")

    with pytest.raises(NotFileOwnerError):
        service.get_status(file_id=uuid.uuid4(), requesting_user_id="someone-else")


def test_get_status_returns_metadata_with_no_signed_url_when_none_is_active(
    service: StatusService, file_repository: Mock, signed_url_repository: Mock
) -> None:
    file_repository.get.return_value = Mock(
        user_id="owner", filename="a.txt", byte_length=10, uploaded_at=datetime.now(timezone.utc)
    )
    signed_url_repository.get_active.return_value = None

    result = service.get_status(file_id=uuid.uuid4(), requesting_user_id="owner")

    assert result.filename == "a.txt"
    assert result.byte_length == 10
    assert result.signed_url is None


def test_get_status_includes_the_active_signed_url_when_present(
    service: StatusService, file_repository: Mock, signed_url_repository: Mock
) -> None:
    file_repository.get.return_value = Mock(
        user_id="owner", filename="a.txt", byte_length=10, uploaded_at=datetime.now(timezone.utc)
    )
    signed_url_repository.get_active.return_value = Mock(signed_url="http://example/token")

    result = service.get_status(file_id=uuid.uuid4(), requesting_user_id="owner")

    assert result.signed_url == "http://example/token"
