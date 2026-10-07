from unittest.mock import Mock

from sqlalchemy.orm import Session

from app.models import TransformerCache
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


def test_cache_miss_calls_transformer(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(db_session, transformer)

    result = service.transform("hello")

    assert result == "HELLO"
    transformer.transform.assert_called_once_with("hello")


def test_cache_hit_does_not_call_transformer(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    db_session.add(
        TransformerCache(
            input_hash="2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
            original_input="hello",
            transformed_output="HELLO",
        )
    )
    db_session.commit()
    service = TransformerCacheService(db_session, transformer)

    result = service.transform("hello")

    assert result == "HELLO"
    transformer.transform.assert_not_called()


def test_cache_miss_persists_result(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(db_session, transformer)

    service.transform("hello")
    db_session.commit()

    entry = db_session.query(TransformerCache).filter_by(original_input="hello").one()
    assert entry.transformed_output == "HELLO"


def test_cache_insert_rolls_back_with_outer_transaction(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(db_session, transformer)

    service.transform("hello")
    db_session.rollback()

    entry = db_session.query(TransformerCache).filter_by(original_input="hello").first()
    assert entry is None


def test_repeated_requests_reuse_cached_result(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.return_value = "HELLO"
    service = TransformerCacheService(db_session, transformer)

    first_result = service.transform("hello")
    db_session.commit()
    second_result = service.transform("hello")

    assert first_result == second_result == "HELLO"
    transformer.transform.assert_called_once_with("hello")
