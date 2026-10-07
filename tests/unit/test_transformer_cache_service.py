from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import initialize_database
from app.models import TransformerCache
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'transformer.sqlite3'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as database_session:
        yield database_session
    engine.dispose()


def test_cache_miss_calls_transformer(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(session, transformer)

    result = service.transform("hello")

    assert result == "HELLO"
    transformer.transform.assert_called_once_with("hello")


def test_cache_hit_does_not_call_transformer(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    session.add(
        TransformerCache(
            input_hash="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            original_input="hello",
            transformed_output="HELLO",
        )
    )
    session.commit()
    service = TransformerCacheService(session, transformer)

    result = service.transform("hello")

    assert result == "HELLO"
    transformer.transform.assert_not_called()


def test_cache_miss_persists_result(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(session, transformer)

    service.transform("hello")
    session.commit()

    entry = session.query(TransformerCache).filter_by(original_input="hello").one()
    assert entry.transformed_output == "HELLO"


def test_repeated_requests_reuse_cached_result(session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(session, transformer)

    first_result = service.transform("hello")
    session.commit()
    second_result = service.transform("hello")

    assert first_result == second_result == "HELLO"
    transformer.transform.assert_called_once_with("hello")
