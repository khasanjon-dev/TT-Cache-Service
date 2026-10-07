import pytest
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.core.config import Settings
from app.database import Base, create_database_engine


def test_database_url_can_be_configured_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    configured_url = "postgresql+psycopg://user:pass@db.example:5432/cache_test"
    monkeypatch.setenv("CACHE_DATABASE_URL", configured_url)

    settings = Settings(_env_file=None)

    assert settings.database_url == configured_url


def test_database_engine_uses_postgresql_driver() -> None:
    database_url = "postgresql+psycopg://user:pass@localhost:5432/cache_test"

    engine = create_database_engine(database_url)

    assert engine.dialect.name == "postgresql"
    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.database == "cache_test"
    engine.dispose()


def test_database_session_dependency_closes_session(
    monkeypatch: pytest.MonkeyPatch,
    db_engine,
) -> None:
    factory = sessionmaker(bind=db_engine)
    monkeypatch.setattr(database, "SessionLocal", factory)
    dependency = database.get_db_session()
    session = next(dependency)

    session.begin()
    dependency.close()

    assert not session.in_transaction()


def test_model_base_is_declarative() -> None:
    assert hasattr(Base, "metadata")
