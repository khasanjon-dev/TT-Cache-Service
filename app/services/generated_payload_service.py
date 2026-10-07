"""Deduplicate generated payloads by their original request."""

import json
from hashlib import sha256

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import generated_payload_repository
from app.services.payload_generation_service import PayloadGenerationService


class GeneratedPayloadService:
    """Return existing payload IDs or generate and persist new payloads."""

    def __init__(self, session: Session, payload_generator: PayloadGenerationService) -> None:
        self._session = session
        self._payload_generator = payload_generator

    def get_or_create(self, list_1: list[str], list_2: list[str]) -> str:
        """Return the ID for this request, generating its payload only when absent."""
        request_hash = self._request_hash(list_1, list_2)
        existing = generated_payload_repository.get_by_request_hash(self._session, request_hash)
        if existing is not None:
            return existing.payload_id

        generated_output = self._payload_generator.generate(list_1, list_2)
        try:
            # The unique request-hash constraint arbitrates concurrent inserts.
            # A savepoint keeps a losing insert from aborting the outer transaction.
            with self._session.begin_nested():
                payload = generated_payload_repository.add_payload(
                    self._session,
                    request_hash=request_hash,
                    generated_output=generated_output,
                )
        except IntegrityError:
            existing = generated_payload_repository.get_by_request_hash(self._session, request_hash)
            if existing is None:
                raise
            return existing.payload_id

        return payload.payload_id

    def get_output(self, payload_id: str) -> str | None:
        """Return the formatted payload output, or ``None`` when it is missing."""
        payload = generated_payload_repository.get_by_payload_id(self._session, payload_id)
        if payload is None:
            return None
        return ", ".join(payload.generated_output)

    @staticmethod
    def _request_hash(list_1: list[str], list_2: list[str]) -> str:
        """Hash a stable JSON representation that preserves both list boundaries."""
        canonical_request = json.dumps(
            [list_1, list_2],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return sha256(canonical_request.encode("utf-8")).hexdigest()
