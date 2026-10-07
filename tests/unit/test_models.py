from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import initialize_database
from app.models import GeneratedPayload, TransformerCache


@pytest.fixture
def session(tmp_path: Path) -> Iterator[Session]:
    engine = create_engine(f"sqlite:///{tmp_path / 'models.sqlite3'}")
    initialize_database(engine)
    with Session(engine) as database_session:
        yield database_session
    engine.dispose()


def test_initialization_creates_both_model_tables(session: Session) -> None:
    table_names = set(inspect(session.get_bind()).get_table_names())

    assert table_names == {"generated_payloads", "transformer_cache"}


def test_transformer_input_hash_is_unique(session: Session) -> None:
    session.add_all(
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
        session.commit()


def test_generated_request_hash_is_unique(session: Session) -> None:
    session.add_all(
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
        session.commit()
