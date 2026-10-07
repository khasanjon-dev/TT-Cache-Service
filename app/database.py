"""SQLAlchemy database infrastructure."""

from collections.abc import Generator

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for persistence models."""


def create_database_engine(database_path: str | None = None) -> Engine:
    """Create a SQLite engine for the configured database file."""
    path = database_path or str(get_settings().database_path)
    url = URL.create("sqlite", database=path)
    return create_engine(url, connect_args={"check_same_thread": False})


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a request-scoped session and close it after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialize_database(target_engine: Engine = engine) -> None:
    """Create tables for the registered models during development or tests."""
    # Importing the model package registers all models with Base.metadata.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=target_engine)


if __name__ == "__main__":
    initialize_database()
