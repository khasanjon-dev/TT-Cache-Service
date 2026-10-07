"""Persistence model for generated and deduplicated payloads."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GeneratedPayload(Base):
    """Store generated output once per deterministic original-request hash."""

    __tablename__ = "generated_payloads"
    __table_args__ = (
        UniqueConstraint("request_hash", name="uq_generated_payloads_request_hash"),
    )

    payload_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_output: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
