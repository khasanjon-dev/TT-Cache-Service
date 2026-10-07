from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import initialize_database
from app.models import GeneratedPayload
from app.services.generated_payload_service import GeneratedPayloadService
from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'generated-payload.sqlite3'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as database_session:
        yield database_session
    engine.dispose()


def test_first_request_generates_and_persists_payload(session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.return_value = ["FIRST", "OTHER"]
    service = GeneratedPayloadService(session, generator)

    payload_id = service.get_or_create(["first"], ["other"])
    session.commit()

    payload = session.get(GeneratedPayload, payload_id)
    assert payload is not None
    assert payload.generated_output == ["FIRST", "OTHER"]
    generator.generate.assert_called_once_with(["first"], ["other"])


def test_identical_request_returns_same_payload_id(session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.return_value = ["FIRST", "OTHER"]
    service = GeneratedPayloadService(session, generator)

    first_id = service.get_or_create(["first"], ["other"])
    session.commit()
    second_id = service.get_or_create(["first"], ["other"])

    assert second_id == first_id
    generator.generate.assert_called_once_with(["first"], ["other"])


def test_different_requests_create_different_payload_ids(session: Session) -> None:
    generator = Mock(spec=PayloadGenerationService)
    generator.generate.side_effect = lambda first, second: first + second
    service = GeneratedPayloadService(session, generator)

    first_id = service.get_or_create(["ab"], ["c"])
    second_id = service.get_or_create(["a"], ["bc"])

    assert first_id != second_id
    assert len(session.scalars(select(GeneratedPayload)).all()) == 2
    assert generator.generate.call_count == 2


def test_existing_payload_skips_transformer(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.side_effect = lambda value: value.upper()
    cache = TransformerCacheService(session, transformer)
    generator = PayloadGenerationService(cache)
    service = GeneratedPayloadService(session, generator)

    first_id = service.get_or_create(["first"], ["other"])
    session.commit()
    second_id = service.get_or_create(["first"], ["other"])

    assert second_id == first_id
    assert transformer.transform.call_count == 2
