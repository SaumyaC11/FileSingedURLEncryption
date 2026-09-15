from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import get_upload_service
from app.schemas import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(tags=["upload"])


@router.post("/v1/upload", response_model=UploadResponse)
async def upload_file(
    user_id: Annotated[str, Form(min_length=1)],
    file: Annotated[UploadFile, File()],
    upload_service: Annotated[UploadService, Depends(get_upload_service)],
) -> UploadResponse:
    content = await file.read()
    record = upload_service.upload(
        user_id=user_id,
        filename=file.filename or "unnamed",
        file_type=file.content_type or "application/octet-stream",
        content=content,
    )
    return UploadResponse(file_id=record.file_id)
