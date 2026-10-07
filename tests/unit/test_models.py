import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import GeneratedPayload, TransformerCache


def test_initialization_creates_both_model_tables(db_engine) -> None:
    table_names = set(inspect(db_engine).get_table_names())

    assert table_names == {"generated_payloads", "transformer_cache"}


def test_transformer_input_hash_is_unique(db_session: Session) -> None:
    db_session.add_all(
        [
            TransformerCache(
                input_hash="a" * 64,
                original_input="first",
                transformed_output="FIRST",
            ),
            TransformerCache(
                input_hash="a" * 64,
                original_input="second",
                transformed_output="SECOND",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_generated_request_hash_is_unique(db_session: Session) -> None:
    db_session.add_all(
        [
            GeneratedPayload(
                payload_id="00000000-0000-0000-0000-000000000001",
                request_hash="b" * 64,
                generated_output=["one"],
            ),
            GeneratedPayload(
                payload_id="00000000-0000-0000-0000-000000000002",
                request_hash="b" * 64,
                generated_output=["two"],
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
