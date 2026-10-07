"""Dependencies used to compose application services for API requests."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.services.generated_payload_service import GeneratedPayloadService
from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer import SimulatedExternalTransformer
from app.services.transformer_cache_service import TransformerCacheService


def get_generated_payload_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> GeneratedPayloadService:
    """Build payload services using the request's database session."""
    transformer_cache = TransformerCacheService(session, SimulatedExternalTransformer())
    payload_generator = PayloadGenerationService(transformer_cache)
    return GeneratedPayloadService(session, payload_generator)
