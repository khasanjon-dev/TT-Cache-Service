"""HTTP endpoints for creating and retrieving generated payloads."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_generated_payload_service
from app.api.schemas.payload import (
    PayloadCreateRequest,
    PayloadCreateResponse,
    PayloadResponse,
)
from app.database import get_db_session
from app.services.generated_payload_service import GeneratedPayloadService

router = APIRouter(prefix="/payload", tags=["payloads"])


@router.post(
    "",
    response_model=PayloadCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payload(
    request: PayloadCreateRequest,
    service: Annotated[GeneratedPayloadService, Depends(get_generated_payload_service)],
    session: Annotated[Session, Depends(get_db_session)],
) -> PayloadCreateResponse:
    """Generate a payload or return the ID of an identical prior request."""
    payload_id = service.get_or_create(request.list_1, request.list_2)
    session.commit()
    return PayloadCreateResponse(payload_id=payload_id)


@router.get("/{payload_id}", response_model=PayloadResponse)
def get_payload(
    payload_id: str,
    service: Annotated[GeneratedPayloadService, Depends(get_generated_payload_service)],
) -> PayloadResponse:
    """Return formatted output for a generated payload."""
    output = service.get_output(payload_id)
    if output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payload not found")
    return PayloadResponse(output=output)
