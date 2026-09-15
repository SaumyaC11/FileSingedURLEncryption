from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_file_retrieval_service
from app.main import app
from app.services.file_retrieval_service import (
    ExpiredSignedToken,
    FileNotFoundError,
    InvalidSignedToken,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


def test_return_file_streams_the_resolved_file(client: TestClient, tmp_path: Path) -> None:
    file_path = tmp_path / "report.txt"
    file_path.write_bytes(b"file contents")
    fake_service = Mock()
    fake_service.resolve.return_value = Mock(
        storage_path=str(file_path), filename="report.txt", file_type="text/plain"
    )
    app.dependency_overrides[get_file_retrieval_service] = lambda: fake_service

    response = client.get("/v1/returnFile", params={"token": "valid-token"})

    assert response.status_code == 200
    assert response.content == b"file contents"


def test_return_file_returns_401_for_an_invalid_token(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.resolve.side_effect = InvalidSignedToken("bad signature")
    app.dependency_overrides[get_file_retrieval_service] = lambda: fake_service

    response = client.get("/v1/returnFile", params={"token": "bad-token"})

    assert response.status_code == 401


def test_return_file_returns_410_for_an_expired_token(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.resolve.side_effect = ExpiredSignedToken("expired")
    app.dependency_overrides[get_file_retrieval_service] = lambda: fake_service

    response = client.get("/v1/returnFile", params={"token": "expired-token"})

    assert response.status_code == 410


def test_return_file_returns_404_when_the_file_no_longer_exists(client: TestClient) -> None:
    fake_service = Mock()
    fake_service.resolve.side_effect = FileNotFoundError("gone")
    app.dependency_overrides[get_file_retrieval_service] = lambda: fake_service

    response = client.get("/v1/returnFile", params={"token": "valid-token"})

    assert response.status_code == 404
