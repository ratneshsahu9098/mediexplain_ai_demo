"""AI-generated explanation records (never treated as verified results)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import utcnow


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(
        ForeignKey("test_results.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(20), default="en")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(120), default="template")
    source: Mapped[str] = mapped_column(String(60), default="template")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    result: Mapped["TestResult"] = relationship(back_populates="explanations")  # noqa: F821
