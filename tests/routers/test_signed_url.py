import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_signed_url_service
from app.main import app
from app.services.signed_url_service import (
    ActiveSignedURLExistsError,
    FileNotFoundError,
    NotFileOwnerError,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def _request_body(**overrides) -> dict:
    body = {
        "file_id": str(uuid.uuid4()),
        "ttl_seconds": 3600,
        "requesting_user_id": "user-1",
    }
    body.update(overrides)
    return body


def test_generate_signed_url_returns_the_url_and_expiry(client: TestClient) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    fake_service = Mock()
    fake_service.generate.return_value = Mock(
        signed_url="http://localhost:8000/v1/returnFile?token=abc", expires_at=expires_at
    )
    app.dependency_overrides[get_signed_url_service] = lambda: fake_service

    response = client.post("/v1/generateSignedURL", json=_request_body())

    assert response.status_code == 200
    assert response.json()["signed_url"] == "http://localhost:8000/v1/returnFile?token=abc"


def test_generate_signed_url_returns_404_when_the_file_is_missing(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.generate.side_effect = FileNotFoundError("nope")
    app.dependency_overrides[get_signed_url_service] = lambda: fake_service

    response = client.post("/v1/generateSignedURL", json=_request_body())

    assert response.status_code == 404


def test_generate_signed_url_returns_403_when_the_requester_is_not_the_owner(
    client: TestClient,
) -> None:
    fake_service = Mock()
    fake_service.generate.side_effect = NotFileOwnerError("not yours")
    app.dependency_overrides[get_signed_url_service] = lambda: fake_service

    response = client.post("/v1/generateSignedURL", json=_request_body())

    assert response.status_code == 403


def test_generate_signed_url_returns_409_when_an_active_url_already_exists(
    client: TestClient,
) -> None:
    fake_service = Mock()
    fake_service.generate.side_effect = ActiveSignedURLExistsError("already active")
    app.dependency_overrides[get_signed_url_service] = lambda: fake_service

    response = client.post("/v1/generateSignedURL", json=_request_body())

    assert response.status_code == 409


@pytest.mark.parametrize("ttl_seconds", [0, -1])
def test_generate_signed_url_rejects_a_non_positive_ttl(
    client: TestClient, ttl_seconds: int
) -> None:
    response = client.post(
        "/v1/generateSignedURL", json=_request_body(ttl_seconds=ttl_seconds)
    )

    assert response.status_code == 422
