from unittest.mock import Mock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GeneratedPayload, TransformerCache
from app.services.generated_payload_service import GeneratedPayloadService
from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


def test_first_request_generates_and_persists_payload(db_session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.return_value = ["FIRST", "OTHER"]
    service = GeneratedPayloadService(db_session, generator)

    payload_id = service.get_or_create(["first"], ["other"])
    db_session.commit()

    payload = db_session.get(GeneratedPayload, payload_id)
    assert payload is not None
    assert payload.generated_output == ["FIRST", "OTHER"]
    generator.generate.assert_called_once_with(["first"], ["other"])


def test_identical_request_returns_same_payload_id(db_session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.return_value = ["FIRST", "OTHER"]
    service = GeneratedPayloadService(db_session, generator)

    first_id = service.get_or_create(["first"], ["other"])
    db_session.commit()
    second_id = service.get_or_create(["first"], ["other"])

    assert second_id == first_id
    generator.generate.assert_called_once_with(["first"], ["other"])


def test_different_requests_create_different_payload_ids(db_session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.side_effect = lambda first, second: first + second
    service = GeneratedPayloadService(db_session, generator)

    first_id = service.get_or_create(["ab"], ["c"])
    second_id = service.get_or_create(["a"], ["bc"])

    assert first_id != second_id
    assert len(db_session.scalars(select(GeneratedPayload)).all()) == 2
    assert generator.generate.call_count == 2


def test_existing_payload_skips_transformer(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.side_effect = lambda value: value.upper()
    cache = TransformerCacheService(db_session, transformer)
    generator = PayloadGenerationService(cache)
    service = GeneratedPayloadService(db_session, generator)

    first_id = service.get_or_create(["first"], ["other"])
    db_session.commit()
    second_id = service.get_or_create(["first"], ["other"])

    assert second_id == first_id
    assert transformer.transform.call_count == 2


def test_payload_and_cache_inserts_roll_back_together(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.side_effect = lambda value: value.upper()
    cache = TransformerCacheService(db_session, transformer)
    generator = PayloadGenerationService(cache)
    service = GeneratedPayloadService(db_session, generator)

    payload_id = service.get_or_create(["first"], ["other"])
    db_session.rollback()

    assert db_session.get(GeneratedPayload, payload_id) is None
    assert db_session.scalars(select(TransformerCache)).all() == []
