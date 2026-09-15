import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: uuid.UUID


class GenerateSignedURLRequest(BaseModel):
    file_id: uuid.UUID
    ttl_seconds: int = Field(gt=0, le=30 * 24 * 3600, description="Time-to-live in seconds")
    requesting_user_id: str = Field(min_length=1)


class GenerateSignedURLResponse(BaseModel):
    signed_url: str
    expires_at: datetime


class FileStatusResponse(BaseModel):
    filename: str
    byte_length: int
    uploaded_at: datetime
    signed_url: str | None = None
