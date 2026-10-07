from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import initialize_database
from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'payload.sqlite3'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as database_session:
        yield database_session
    engine.dispose()


def test_generate_interleaves_transformed_values() -> None:
    cache = Mock(spec=TransformerCacheService)
    cache.transform.side_effect = lambda value: value.upper()
    service = PayloadGenerationService(cache)

    result = service.generate(
        ["first", "second", "third"],
        ["other", "another", "last"],
    )

    assert result == ["FIRST", "OTHER", "SECOND", "ANOTHER", "THIRD", "LAST"]
    assert [call.args[0] for call in cache.transform.call_args_list] == [
        "first",
        "other",
        "second",
        "another",
        "third",
        "last",
    ]


def test_generate_accepts_empty_lists() -> None:
    cache = Mock(spec=TransformerCacheService)
    service = PayloadGenerationService(cache)

    assert service.generate([], []) == []
    cache.transform.assert_not_called()


def test_generate_rejects_unequal_lists_before_transforming() -> None:
    cache = Mock(spec=TransformerCacheService)
    service = PayloadGenerationService(cache)

    with pytest.raises(ValueError, match="same length"):
        service.generate(["first"], [])

    cache.transform.assert_not_called()


def test_generate_reuses_transformer_cache(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.side_effect = lambda value: value.upper()
    cache = TransformerCacheService(session, transformer)
    service = PayloadGenerationService(cache)

    first_result = service.generate(["hello", "world"], ["hello", "again"])
    session.commit()
    second_result = service.generate(["hello", "world"], ["hello", "again"])

    assert first_result == second_result == ["HELLO", "HELLO", "WORLD", "AGAIN"]
    assert transformer.transform.call_count == 3
