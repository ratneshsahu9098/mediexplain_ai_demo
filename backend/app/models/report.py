"""Medical report and extracted test-result models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import utcnow


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    report_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    status: Mapped[str] = mapped_column(String(30), default="processing", index=True)
    extraction_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="reports")  # noqa: F821
    results: Mapped[list["TestResult"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="TestResult.id",
    )
    chat_messages: Mapped[list["ChatMessage"]] = relationship(  # noqa: F821
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )

    test_name: Mapped[str] = mapped_column(String(150), nullable=False)
    raw_name: Mapped[str] = mapped_column(String(200), default="")
    canonical_name: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_text: Mapped[str] = mapped_column(String(80), default="")
    unit: Mapped[str] = mapped_column(String(40), default="")

    range_low: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    range_high: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    range_text: Mapped[str] = mapped_column(String(80), default="")
    range_unit: Mapped[str] = mapped_column(String(40), default="")

    status: Mapped[str] = mapped_column(String(30), default="UNKNOWN", index=True)
    report_flag: Mapped[str] = mapped_column(String(20), default="")
    unit_converted: Mapped[bool] = mapped_column(Boolean, default=False)
    critical_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_page: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, default="")

    report: Mapped["Report"] = relationship(back_populates="results")
    explanations: Mapped[list["Explanation"]] = relationship(  # noqa: F821
        back_populates="result",
        cascade="all, delete-orphan",
        order_by="Explanation.id",
    )
