"""Business logic for transforming inputs with database-backed caching."""

from hashlib import sha256

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import transformer_cache_repository
from app.services.transformer import Transformer


class TransformerCacheService:
    """Coordinate cache lookups, transformer calls, and cache persistence."""

    def __init__(self, session: Session, transformer: Transformer) -> None:
        self._session = session
        self._transformer = transformer

    def transform(self, value: str) -> str:
        """Return a cached result or transform and cache the input."""
        input_hash = sha256(value.encode("utf-8")).hexdigest()
        cached = transformer_cache_repository.get_by_input_hash(self._session, input_hash)
        if cached is not None:
            if cached.original_input != value:
                raise RuntimeError("SHA-256 collision detected in transformer cache")
            return cached.transformed_output

        transformed_output = self._transformer.transform(value)
        try:
            # Keep the insert isolated so a uniqueness race does not invalidate
            # other work in the caller's transaction.
            with self._session.begin_nested():
                transformer_cache_repository.add_cache_entry(
                    self._session,
                    input_hash=input_hash,
                    original_input=value,
                    transformed_output=transformed_output,
                )
        except IntegrityError as error:
            cached = transformer_cache_repository.get_by_input_hash(self._session, input_hash)
            if cached is None:
                raise
            if cached.original_input != value:
                raise RuntimeError("SHA-256 collision detected in transformer cache") from error
            return cached.transformed_output

        return transformed_output
