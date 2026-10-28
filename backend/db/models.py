"""
SQLAlchemy tables:
  requests   - every processed repair-authorization request (+ audit fields)
  guidelines - carrier guidelines with a pgvector embedding for semantic search
"""
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Boolean, Float, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base

EMBEDDING_DIM = 384  # sentence-transformers all-MiniLM-L6-v2


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RequestRecord(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    claim_number: Mapped[str] = mapped_column(String(40), index=True)
    policyholder_name: Mapped[str] = mapped_column(String(200))
    carrier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    vehicle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    service_code: Mapped[str] = mapped_column(String(40), index=True)
    service_name: Mapped[str] = mapped_column(String(300))
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    note_text: Mapped[str] = mapped_column(Text)

    preapproval_required: Mapped[bool] = mapped_column(Boolean)
    guideline_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    criteria: Mapped[list] = mapped_column(JSON, default=list)
    trace: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # Human-in-the-loop override (null until a reviewer acts)
    overridden: Mapped[bool] = mapped_column(Boolean, default=False)
    override_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_by: Mapped[str | None] = mapped_column(String(120), nullable=True)


class GuidelineRecord(Base):
    __tablename__ = "guidelines"

    guideline_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    carrier_name: Mapped[str] = mapped_column(String(200))
    service_code: Mapped[str] = mapped_column(String(40), index=True)
    service_name: Mapped[str] = mapped_column(String(300))
    preapproval_required: Mapped[bool] = mapped_column(Boolean)
    criteria: Mapped[list] = mapped_column(JSON, default=list)
    guideline_text: Mapped[str] = mapped_column(Text)
    # Nullable: seeding works even without the optional ML dependencies
    embedding: Mapped[list | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
