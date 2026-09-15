from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = (
        "postgresql+psycopg://fileservice:fileservice_dev_pw@localhost:5432/fileservice"
    )

    # Non-public directory where uploaded file contents are stored.
    storage_dir: Path = Path("storage/uploads")

    # Must stay stable across restarts so previously issued signed URLs keep validating.
    signed_url_secret_key: str = "dev-only-insecure-secret-change-me"
    signed_url_salt: str = "signed-url"

    # Used to build the fully-qualified signed URL returned to clients.
    base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
