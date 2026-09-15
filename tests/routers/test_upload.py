import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_upload_service
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_upload_returns_the_created_file_id(client: TestClient) -> None:
    file_id = uuid.uuid4()
    fake_service = Mock()
    fake_service.upload.return_value = Mock(file_id=file_id)
    app.dependency_overrides[get_upload_service] = lambda: fake_service

    response = client.post(
        "/v1/upload",
        data={"user_id": "user-1"},
        files={"file": ("report.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json() == {"file_id": str(file_id)}


def test_upload_passes_the_file_contents_and_metadata_to_the_service(
    client: TestClient,
) -> None:
    fake_service = Mock()
    fake_service.upload.return_value = Mock(file_id=uuid.uuid4())
    app.dependency_overrides[get_upload_service] = lambda: fake_service

    client.post(
        "/v1/upload",
        data={"user_id": "user-1"},
        files={"file": ("report.txt", b"hello", "text/plain")},
    )

    fake_service.upload.assert_called_once_with(
        user_id="user-1",
        filename="report.txt",
        file_type="text/plain",
        content=b"hello",
    )


def test_upload_requires_a_non_empty_user_id(client: TestClient) -> None:
    response = client.post(
        "/v1/upload",
        data={"user_id": ""},
        files={"file": ("report.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
