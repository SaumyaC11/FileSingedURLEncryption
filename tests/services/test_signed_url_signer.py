import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.signed_url_signer import (
    ExpiredSignedToken,
    InvalidSignedToken,
    SignedURLSigner,
)


@pytest.fixture
def signer() -> SignedURLSigner:
    return SignedURLSigner("test-secret-key", "test-salt")


def test_sign_then_unsign_returns_the_original_file_id(signer: SignedURLSigner) -> None:
    file_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    token = signer.sign(file_id, expires_at)

    assert signer.unsign(token) == file_id


def test_unsign_rejects_a_token_with_a_bad_signature(signer: SignedURLSigner) -> None:
    file_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = signer.sign(file_id, expires_at)

    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(InvalidSignedToken):
        signer.unsign(tampered)


def test_unsign_rejects_a_token_signed_with_a_different_key(signer: SignedURLSigner) -> None:
    file_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = signer.sign(file_id, expires_at)

    other_signer = SignedURLSigner("a-different-secret-key", "test-salt")

    with pytest.raises(InvalidSignedToken):
        other_signer.unsign(token)


def test_unsign_rejects_an_expired_token(signer: SignedURLSigner) -> None:
    file_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    token = signer.sign(file_id, expires_at)

    with pytest.raises(ExpiredSignedToken):
        signer.unsign(token)
