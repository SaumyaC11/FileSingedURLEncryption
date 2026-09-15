import uuid
from unittest.mock import Mock

import pytest

from app.services.signed_url_service import (
    ActiveSignedURLExistsError,
    FileNotFoundError,
    NotFileOwnerError,
    SignedURLService,
)


@pytest.fixture
def collaborators() -> dict[str, Mock]:
    return {
        "signer": Mock(),
        "file_repository": Mock(),
        "signed_url_repository": Mock(),
        "audit_repository": Mock(),
    }


@pytest.fixture
def service(collaborators: dict[str, Mock]) -> SignedURLService:
    return SignedURLService(
        signer=collaborators["signer"],
        file_repository=collaborators["file_repository"],
        signed_url_repository=collaborators["signed_url_repository"],
        audit_repository=collaborators["audit_repository"],
        base_url="http://localhost:8000/",
    )


def test_generate_raises_when_the_file_does_not_exist(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    collaborators["file_repository"].get.return_value = None

    with pytest.raises(FileNotFoundError):
        service.generate(file_id=uuid.uuid4(), ttl_seconds=60, requesting_user_id="user-1")


def test_generate_raises_when_the_requester_is_not_the_owner(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    collaborators["file_repository"].get.return_value = Mock(user_id="owner")

    with pytest.raises(NotFileOwnerError):
        service.generate(file_id=uuid.uuid4(), ttl_seconds=60, requesting_user_id="someone-else")


def test_generate_raises_when_an_active_signed_url_already_exists(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    collaborators["file_repository"].get.return_value = Mock(user_id="user-1")
    collaborators["signed_url_repository"].get_active.return_value = Mock()

    with pytest.raises(ActiveSignedURLExistsError):
        service.generate(file_id=uuid.uuid4(), ttl_seconds=60, requesting_user_id="user-1")


def test_generate_builds_a_return_file_url_using_the_signed_token(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    collaborators["file_repository"].get.return_value = Mock(user_id="user-1")
    collaborators["signed_url_repository"].get_active.return_value = None
    collaborators["signer"].sign.return_value = "signed-token"

    result = service.generate(file_id=uuid.uuid4(), ttl_seconds=60, requesting_user_id="user-1")

    assert result.signed_url == "http://localhost:8000/v1/returnFile?token=signed-token"


def test_generate_persists_the_signed_url_and_an_audit_event(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    file_id = uuid.uuid4()
    collaborators["file_repository"].get.return_value = Mock(user_id="user-1")
    collaborators["signed_url_repository"].get_active.return_value = None
    collaborators["signer"].sign.return_value = "signed-token"

    result = service.generate(file_id=file_id, ttl_seconds=60, requesting_user_id="user-1")

    collaborators["signed_url_repository"].create.assert_called_once_with(
        file_id=file_id,
        signed_url=result.signed_url,
        ttl_seconds=60,
        expires_at=result.expires_at,
    )
    collaborators["audit_repository"].record_signed_url_issued.assert_called_once_with(
        file_id=file_id,
        requested_by="user-1",
        expires_at=result.expires_at,
    )


def test_generate_does_not_persist_anything_when_the_file_is_missing(
    service: SignedURLService, collaborators: dict[str, Mock]
) -> None:
    collaborators["file_repository"].get.return_value = None

    with pytest.raises(FileNotFoundError):
        service.generate(file_id=uuid.uuid4(), ttl_seconds=60, requesting_user_id="user-1")

    collaborators["signed_url_repository"].create.assert_not_called()
    collaborators["audit_repository"].record_signed_url_issued.assert_not_called()
