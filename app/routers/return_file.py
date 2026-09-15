from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.dependencies import get_file_retrieval_service
from app.services.file_retrieval_service import (
    ExpiredSignedToken,
    FileNotFoundError,
    FileRetrievalService,
    InvalidSignedToken,
)

router = APIRouter(tags=["return-file"])

# for returning the file
# Validates a signed token and streams back the file it points to.
@router.get("/v1/returnFile")
def return_file(
    token: Annotated[str, Query()],
    file_retrieval_service: Annotated[FileRetrievalService, Depends(get_file_retrieval_service)],
) -> FileResponse:
    try:
        metadata = file_retrieval_service.resolve(token)
    except InvalidSignedToken as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ExpiredSignedToken as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # return file storage path the name of the file and the metadata
    return FileResponse(
        path=metadata.storage_path,
        filename=metadata.filename,
        media_type=metadata.file_type,
    )
