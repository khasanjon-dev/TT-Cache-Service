"""SQLAlchemy database infrastructure."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for persistence models."""


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create a PostgreSQL engine from the configured SQLAlchemy URL."""
    url = make_url(database_url or get_settings().database_url)
    return create_engine(url, pool_pre_ping=True)


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
