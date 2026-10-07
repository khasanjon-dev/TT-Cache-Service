from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database as database
from app.core.config import Settings
from app.database import Base, create_database_engine


def test_database_path_can_be_configured_from_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configured_path = tmp_path / "configured.sqlite3"
    monkeypatch.setenv("CACHE_DATABASE_PATH", str(configured_path))

    settings = Settings(_env_file=None)

    assert settings.database_path == configured_path


def test_database_engine_uses_configured_sqlite_path(tmp_path: Path) -> None:
    database_path = tmp_path / "service.sqlite3"

    engine = create_database_engine(str(database_path))

    assert engine.dialect.name == "sqlite"
    assert engine.url.database == str(database_path)
    engine.dispose()


def test_database_session_dependency_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    test_engine = create_engine("sqlite://")
    factory = sessionmaker(bind=test_engine)
    monkeypatch.setattr(database, "SessionLocal", factory)
    dependency = database.get_db_session()
    session = next(dependency)

    session.begin()
    dependency.close()

    assert not session.in_transaction()
    test_engine.dispose()


def test_model_base_is_declarative() -> None:
    assert hasattr(Base, "metadata")
