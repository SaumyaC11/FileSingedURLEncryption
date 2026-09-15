import uuid

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class InvalidSignedToken(Exception):
    """Raised when a token fails signature or expiry validation."""


class SignedURLSigner:
    """Creates and validates cryptographically signed, stateless file tokens.

    Tokens embed their own signing timestamp, so validity survives a service
    restart as long as the secret key stays the same.
    """

    def __init__(self, secret_key: str, salt: str) -> None:
        self._serializer = URLSafeTimedSerializer(secret_key, salt=salt)

    def sign(self, file_id: uuid.UUID) -> str:
        return self._serializer.dumps({"file_id": str(file_id)})

    def unsign(self, token: str, max_age_seconds: int) -> uuid.UUID:
        try:
            payload = self._serializer.loads(token, max_age=max_age_seconds)
        except (BadSignature, SignatureExpired) as exc:
            raise InvalidSignedToken(str(exc)) from exc
        return uuid.UUID(payload["file_id"])
