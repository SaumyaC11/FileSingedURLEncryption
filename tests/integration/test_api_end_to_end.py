import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client(db_session: Session, tmp_path: Path) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"storage_dir": tmp_path}
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_upload_then_status_then_signed_url_then_download_round_trips_through_postgres(
    client: TestClient,
) -> None:
    upload_response = client.post(
        "/v1/upload",
        data={"user_id": "user-1"},
        files={"file": ("report.txt", b"integration test contents", "text/plain")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["file_id"]

    status_response = client.get(
        f"/v1/status/{file_id}", params={"requesting_user_id": "user-1"}
    )
    assert status_response.status_code == 200
    assert status_response.json()["filename"] == "report.txt"
    assert status_response.json()["signed_url"] is None

    signed_url_response = client.post(
        "/v1/generateSignedURL",
        json={"file_id": file_id, "ttl_seconds": 3600, "requesting_user_id": "user-1"},
    )
    assert signed_url_response.status_code == 200
    signed_url = signed_url_response.json()["signed_url"]
    token = signed_url.split("token=", 1)[1]

    second_signed_url_response = client.post(
        "/v1/generateSignedURL",
        json={"file_id": file_id, "ttl_seconds": 3600, "requesting_user_id": "user-1"},
    )
    assert second_signed_url_response.status_code == 409

    status_after_signing = client.get(
        f"/v1/status/{file_id}", params={"requesting_user_id": "user-1"}
    )
    assert status_after_signing.json()["signed_url"] == signed_url

    download_response = client.get("/v1/returnFile", params={"token": token})
    assert download_response.status_code == 200
    assert download_response.content == b"integration test contents"


def test_status_returns_403_for_a_non_owner(client: TestClient) -> None:
    upload_response = client.post(
        "/v1/upload",
        data={"user_id": "owner"},
        files={"file": ("secret.txt", b"owner-only", "text/plain")},
    )
    file_id = upload_response.json()["file_id"]

    response = client.get(f"/v1/status/{file_id}", params={"requesting_user_id": "someone-else"})

    assert response.status_code == 403


def test_status_returns_404_for_an_unknown_file(client: TestClient) -> None:
    response = client.get(
        f"/v1/status/{uuid.uuid4()}", params={"requesting_user_id": "user-1"}
    )

    assert response.status_code == 404
