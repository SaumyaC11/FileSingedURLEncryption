import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_status_service
from app.schemas import FileStatusResponse
from app.services.status_service import FileNotFoundError, NotFileOwnerError, StatusService

router = APIRouter(tags=["status"])


# Returns a file's metadata and its active signed URL, if the caller owns it.
@router.get("/v1/status/{file_id}", response_model=FileStatusResponse)
def get_file_status(
    file_id: uuid.UUID,
    requesting_user_id: Annotated[str, Query(min_length=1)],
    status_service: Annotated[StatusService, Depends(get_status_service)],
) -> FileStatusResponse:
    try:
        result = status_service.get_status(
            file_id=file_id, requesting_user_id=requesting_user_id
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotFileOwnerError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return FileStatusResponse(
        filename=result.filename,
        byte_length=result.byte_length,
        uploaded_at=result.uploaded_at,
        signed_url=result.signed_url,
    )
