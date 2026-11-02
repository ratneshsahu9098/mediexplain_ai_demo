"""Pydantic schemas: reports, results and explanations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import UTCDateTime


class ExplanationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language: str
    text: str
    model: str
    source: str


class TestResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_name: str
    raw_name: str
    canonical_name: Optional[str] = None
    value: Optional[float] = None
    value_text: str
    unit: str
    range_low: Optional[float] = None
    range_high: Optional[float] = None
    range_text: str
    range_unit: str
    status: str
    report_flag: str
    unit_converted: bool
    critical_flag: bool
    confidence: float
    source_page: int
    notes: str
    # Most recent explanation, if one has been generated.
    explanation: Optional[str] = None
    explanation_source: Optional[str] = None


class ReportSummary(BaseModel):
    id: int
    original_filename: str
    report_type: str
    status: str
    extraction_method: Optional[str] = None
    page_count: int
    result_count: int
    abnormal_count: int
    created_at: UTCDateTime


class ReportDetail(BaseModel):
    id: int
    original_filename: str
    report_type: str
    status: str
    extraction_method: Optional[str] = None
    page_count: int
    error_message: Optional[str] = None
    created_at: UTCDateTime
    result_count: int
    abnormal_count: int
    results: list[TestResultOut]
    disclaimer: str


class ReportListResponse(BaseModel):
    total: int
    items: list[ReportSummary]


class AnalyzeResponse(BaseModel):
    report_id: int
    abnormal_count: int
    results: list[TestResultOut]


class ExplanationItem(BaseModel):
    result_id: int
    test_name: str
    text: str
    model: str
    source: str


class ExplainResponse(BaseModel):
    report_id: int
    language: str
    provider: str
    explanations: list[ExplanationItem]
    disclaimer: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", max_length=20)

    @field_validator("message")
    @classmethod
    def _message_must_have_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be empty.")
        return cleaned

    @field_validator("language")
    @classmethod
    def _normalise_language(cls, value: str) -> str:
        return value.strip().lower()


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    language: str
    model: str
    source: str
    cited_result_ids: list[int] = Field(default_factory=list)
    created_at: UTCDateTime


class ChatResponse(BaseModel):
    report_id: int
    language: str
    provider: str
    reply: ChatMessageOut
    disclaimer: str


class ChatHistoryResponse(BaseModel):
    report_id: int
    messages: list[ChatMessageOut]
    disclaimer: str


DISCLAIMER = (
    "MediExplain AI is an educational tool, not a diagnostic system. "
    "An out-of-range value is not a diagnosis. Always discuss your results "
    "with a qualified healthcare professional."
)

EXPLANATION_DISCLAIMER = (
    "AI-generated educational content. It is not verified medical advice and "
    "must not be used to diagnose, treat or decide on medication."
)

CHAT_DISCLAIMER = (
    "AI-generated conversation about this report only. It is not verified "
    "medical advice, cannot diagnose or prescribe, and must not replace a "
    "consultation with a qualified healthcare professional."
)
