from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.services.payload_generation_service import PayloadGenerationService
from app.services.transformer import Transformer
from app.services.transformer_cache_service import TransformerCacheService


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


def test_generate_reuses_transformer_cache(db_session: Session) -> None:
    transformer = Mock(spec=Transformer)
    transformer.transform.side_effect = lambda value: value.upper()
    cache = TransformerCacheService(db_session, transformer)
    service = PayloadGenerationService(cache)

    first_result = service.generate(["hello", "world"], ["hello", "again"])
    db_session.commit()
    second_result = service.generate(["hello", "world"], ["hello", "again"])

    assert first_result == second_result == ["HELLO", "HELLO", "WORLD", "AGAIN"]
    assert transformer.transform.call_count == 3
