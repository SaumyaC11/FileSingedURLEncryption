import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_status_service
from app.main import app
from app.services.status_service import FileNotFoundError, NotFileOwnerError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_get_file_status_returns_the_file_status(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.get_status.return_value = Mock(
        filename="report.pdf",
        byte_length=42,
        uploaded_at=datetime.now(timezone.utc),
        signed_url=None,
    )
    app.dependency_overrides[get_status_service] = lambda: fake_service

    response = client.get(
        f"/v1/status/{uuid.uuid4()}", params={"requesting_user_id": "user-1"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "report.pdf"
    assert response.json()["byte_length"] == 42


def test_get_file_status_returns_404_when_the_file_is_missing(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.get_status.side_effect = FileNotFoundError("nope")
    app.dependency_overrides[get_status_service] = lambda: fake_service

    response = client.get(
        f"/v1/status/{uuid.uuid4()}", params={"requesting_user_id": "user-1"}
    )

    assert response.status_code == 404


def test_get_file_status_returns_403_when_the_requester_is_not_the_owner(
    client: TestClient,
) -> None:
    fake_service = Mock()
    fake_service.get_status.side_effect = NotFileOwnerError("not yours")
    app.dependency_overrides[get_status_service] = lambda: fake_service

    response = client.get(
        f"/v1/status/{uuid.uuid4()}", params={"requesting_user_id": "user-1"}
    )

    assert response.status_code == 403


def test_get_file_status_requires_a_non_empty_requesting_user_id(client: TestClient) -> None:
    response = client.get(f"/v1/status/{uuid.uuid4()}", params={"requesting_user_id": ""})

    assert response.status_code == 422


def test_get_file_status_rejects_a_malformed_file_id(client: TestClient) -> None:
    response = client.get("/v1/status/not-a-uuid", params={"requesting_user_id": "user-1"})

    assert response.status_code == 422
