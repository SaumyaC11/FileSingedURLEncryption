from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_signed_url_service
from app.schemas import GenerateSignedURLRequest, GenerateSignedURLResponse
from app.services.signed_url_service import FileNotFoundError, SignedURLService

router = APIRouter(tags=["signed-url"])


@router.post("/v1/generateSignedURL", response_model=GenerateSignedURLResponse)
def generate_signed_url(
    request: GenerateSignedURLRequest,
    signed_url_service: Annotated[SignedURLService, Depends(get_signed_url_service)],
) -> GenerateSignedURLResponse:
    try:
        result = signed_url_service.generate(
            file_id=request.file_id,
            ttl_seconds=request.ttl_seconds,
            requesting_user_id=request.requesting_user_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return GenerateSignedURLResponse(
        signed_url=result.signed_url,
        expires_at=result.expires_at,
    )
