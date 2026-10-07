"""Database operations for generated payloads."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GeneratedPayload


def get_by_request_hash(session: Session, request_hash: str) -> GeneratedPayload | None:
    """Return a payload for the request hash, if one has already been stored."""
    statement = select(GeneratedPayload).where(GeneratedPayload.request_hash == request_hash)
    return session.scalar(statement)


def get_by_payload_id(session: Session, payload_id: str) -> GeneratedPayload | None:
    """Return a payload by its public identifier, if it exists."""
    return session.get(GeneratedPayload, payload_id)


def add_payload(
    session: Session,
    request_hash: str,
    generated_output: list[str],
) -> GeneratedPayload:
    """Add and flush a payload within the current transaction."""
    payload = GeneratedPayload(
        request_hash=request_hash,
        generated_output=generated_output,
    )
    session.add(payload)
    session.flush()
    return payload
