"""Persistence model for cached transformer results."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransformerCache(Base):
    """Store one transformer result for each deterministic input hash."""

    __tablename__ = "transformer_cache"
    __table_args__ = (UniqueConstraint("input_hash", name="uq_transformer_cache_input_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    original_input: Mapped[str] = mapped_column(Text, nullable=False)
    transformed_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
