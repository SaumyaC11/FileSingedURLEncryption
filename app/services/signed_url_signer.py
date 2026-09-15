import uuid
from datetime import datetime, timezone

from itsdangerous import BadSignature, URLSafeSerializer


class InvalidSignedToken(Exception):
    """Raised when a token fails signature validation."""


class ExpiredSignedToken(Exception):
    """Raised when a token's signature is valid but it has expired."""


class SignedURLSigner:
    """Creates and validates cryptographically signed, stateless file tokens.

    The expiry is embedded in the signed payload itself, so validation never
    depends on external state and survives a service restart as long as the
    secret key stays the same.
    """

    # Builds the serializer used to sign and verify tokens.
    def __init__(self, secret_key: str, salt: str) -> None:
        self._serializer = URLSafeSerializer(secret_key, salt=salt)

    # Encodes a file ID and expiry into a signed, stateless token.
    def sign(self, file_id: uuid.UUID, expires_at: datetime) -> str:
        payload = {"file_id": str(file_id), "exp": int(expires_at.timestamp())}
        return self._serializer.dumps(payload)

    # Verifies a token's signature and expiry, returning the file ID it encodes.
    def unsign(self, token: str) -> uuid.UUID:
        try:
            payload = self._serializer.loads(token)
        except BadSignature as exc:
            raise InvalidSignedToken(str(exc)) from exc

        if datetime.now(timezone.utc).timestamp() > payload["exp"]:
            raise ExpiredSignedToken(f"Token expired at {payload['exp']}")

        return uuid.UUID(payload["file_id"])
