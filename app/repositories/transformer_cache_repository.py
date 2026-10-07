"""Database operations for cached transformer results."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TransformerCache


def get_by_input_hash(session: Session, input_hash: str) -> TransformerCache | None:
    """Return the cached transformation for an input hash, if it exists."""
    statement = select(TransformerCache).where(TransformerCache.input_hash == input_hash)
    return session.scalar(statement)


def add_cache_entry(
    session: Session,
    input_hash: str,
    original_input: str,
    transformed_output: str,
) -> TransformerCache:
    """Add and flush one cache entry within the current transaction."""
    entry = TransformerCache(
        input_hash=input_hash,
        original_input=original_input,
        transformed_output=transformed_output,
    )
    session.add(entry)
    session.flush()
    return entry
