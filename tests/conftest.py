"""Shared database fixtures for backend-agnostic and PostgreSQL test runs."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

# Register all model tables before resetting a configured PostgreSQL test DB.
import app.models  # noqa: F401
from app.database import Base, initialize_database


@pytest.fixture
def db_engine(tmp_path: Path) -> Iterator[Engine]:
    """Create an isolated test database, using PostgreSQL when configured."""
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if test_database_url:
        engine = create_engine(test_database_url, pool_pre_ping=True)
    else:
        engine = create_engine(
            f"sqlite:///{tmp_path / 'test.sqlite3'}",
            connect_args={"autocommit": False, "check_same_thread": False},
        )

    Base.metadata.drop_all(engine)
    initialize_database(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """Yield a session bound to the current isolated test database."""
    with Session(db_engine, expire_on_commit=False) as session:
        yield session
