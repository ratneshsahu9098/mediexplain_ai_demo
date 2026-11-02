"""Report upload, retrieval, analysis and explanation routes."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import ChatMessage, Explanation, Report, TestResult, User
from app.schemas.report import (
    AnalyzeResponse,
    CHAT_DISCLAIMER,
    ChatHistoryResponse,
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    DISCLAIMER,
    EXPLANATION_DISCLAIMER,
    ExplainResponse,
    ExplanationItem,
    ReportDetail,
    ReportListResponse,
    ReportSummary,
    TestResultOut,
)
from app.utils.files import safe_original_name, store_upload, validate_upload
from services.ai.llm_provider import get_provider
from services.chat_service import ChatEngine
from services.document_processor import process_document
from services.errors import ProcessingError
from services.explanation_service import (
    LANGUAGES,
    ExplanationEngine,
    ResultContext,
)
from services.medical_analyzer import ABNORMAL_STATUSES, analyze_result
from services.test_parser import ParsedResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

MAX_EXPLANATIONS_PER_REQUEST = 20


def _load_report(db: Session, user_id: int, report_id: int) -> Report:
    report = db.scalar(
        select(Report)
        .where(Report.id == report_id, Report.user_id == user_id)
        .options(
            selectinload(Report.results).selectinload(TestResult.explanations),
        )
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


def _result_out(result: TestResult) -> TestResultOut:
    out = TestResultOut.model_validate(result)
    if result.explanations:
        latest = result.explanations[-1]
        out.explanation = latest.text
        out.explanation_source = latest.source
    return out


def _result_context(result: TestResult) -> ResultContext:
    return ResultContext(
        result_id=result.id,
        test_name=result.test_name,
        canonical_name=result.canonical_name,
        value=result.value,
        value_text=result.value_text,
        unit=result.unit,
        range_low=result.range_low,
        range_high=result.range_high,
        range_text=result.range_text,
        range_unit=result.range_unit,
        status=result.status,
        critical_flag=result.critical_flag,
        confidence=result.confidence,
        extraction_notes=result.notes,
    )


def _report_detail(report: Report) -> ReportDetail:
    results = [_result_out(result) for result in report.results]
    abnormal = sum(1 for result in report.results if result.status in ABNORMAL_STATUSES)
    return ReportDetail(
        id=report.id,
        original_filename=report.original_filename,
        report_type=report.report_type,
        status=report.status,
        extraction_method=report.extraction_method,
        page_count=report.page_count,
        error_message=report.error_message,
        created_at=report.created_at,
        result_count=len(results),
        abnormal_count=abnormal,
        results=results,
        disclaimer=DISCLAIMER,
    )


def _summary(report: Report) -> ReportSummary:
    abnormal = sum(1 for result in report.results if result.status in ABNORMAL_STATUSES)
    return ReportSummary(
        id=report.id,
        original_filename=report.original_filename,
        report_type=report.report_type,
        status=report.status,
        extraction_method=report.extraction_method,
        page_count=report.page_count,
        result_count=len(report.results),
        abnormal_count=abnormal,
        created_at=report.created_at,
    )


def _to_model_value(parsed: ParsedResult) -> dict:
    analysis = analyze_result(parsed)
    return {
        "test_name": parsed.test_name,
        "raw_name": parsed.raw_name,
        "canonical_name": parsed.canonical_name,
        "value": parsed.value,
        "value_text": parsed.value_text,
        "unit": parsed.unit,
        "range_low": parsed.range_low,
        "range_high": parsed.range_high,
        "range_text": parsed.range_text,
        "range_unit": parsed.range_unit,
        "status": analysis.status,
        "report_flag": parsed.report_flag,
        "unit_converted": analysis.unit_converted,
        "critical_flag": analysis.critical_flag,
        "confidence": parsed.confidence,
        "source_page": parsed.source_page,
        "notes": analysis.notes,
    }


@router.post("/upload", response_model=ReportDetail, status_code=status.HTTP_201_CREATED)
async def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportDetail:
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_mb} MB limit.",
        )

    extension, mime_type = validate_upload(file.filename, data)
    digest = hashlib.sha256(data).hexdigest()

    duplicate = db.scalar(
        select(Report).where(
            Report.user_id == current_user.id,
            Report.file_hash == digest,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "This exact file has already been uploaded.",
                "report_id": duplicate.id,
            },
        )

    stored_path = store_upload(settings.upload_path, current_user.id, data, extension)
    report = Report(
        user_id=current_user.id,
        original_filename=safe_original_name(file.filename),
        stored_path=str(stored_path),
        mime_type=mime_type,
        file_size=len(data),
        file_hash=digest,
        status="processing",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    try:
        document = process_document(stored_path, extension)
        for parsed in document.results:
            db.add(TestResult(report_id=report.id, **_to_model_value(parsed)))

        report.report_type = document.report_type
        report.extraction_method = document.extraction_method
        report.page_count = document.page_count
        report.status = "completed"
        if document.warning:
            report.error_message = document.warning
        db.commit()
    except ProcessingError as exc:
        db.rollback()
        _mark_failed(db, report.id, str(exc))
        _delete_file(stored_path)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Report processing failed")
        db.rollback()
        _mark_failed(db, report.id, "Unexpected processing error. Please try again.")
        _delete_file(stored_path)
        raise HTTPException(
            status_code=500,
            detail="Unexpected error while processing the report.",
        ) from exc

    return _report_detail(_load_report(db, current_user.id, report.id))


def _mark_failed(db: Session, report_id: int, message: str) -> None:
    report = db.get(Report, report_id)
    if report is not None:
        report.status = "failed"
        report.error_message = message
        db.commit()


def _delete_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not delete stored file: %s", path.name)


@router.get("", response_model=ReportListResponse)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportListResponse:
    reports = db.scalars(
        select(Report)
        .where(Report.user_id == current_user.id)
        .options(selectinload(Report.results))
        .order_by(Report.created_at.desc(), Report.id.desc())
    ).all()
    items = [_summary(report) for report in reports]
    return ReportListResponse(total=len(items), items=items)


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportDetail:
    return _report_detail(_load_report(db, current_user.id, report_id))


@router.get("/{report_id}/results", response_model=AnalyzeResponse)
def get_results(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    report = _load_report(db, current_user.id, report_id)
    results = [_result_out(result) for result in report.results]
    return AnalyzeResponse(
        report_id=report.id,
        abnormal_count=sum(1 for r in report.results if r.status in ABNORMAL_STATUSES),
        results=results,
    )


@router.post("/{report_id}/analyze", response_model=AnalyzeResponse)
def analyze_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    report = _load_report(db, current_user.id, report_id)
    if report.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only completed reports can be analysed.",
        )

    for stored in report.results:
        parsed = ParsedResult(
            test_name=stored.test_name,
            raw_name=stored.raw_name,
            canonical_name=stored.canonical_name,
            value=stored.value,
            value_text=stored.value_text,
            unit=stored.unit,
            range_low=stored.range_low,
            range_high=stored.range_high,
            range_text=stored.range_text,
            range_unit=stored.range_unit,
            report_flag=stored.report_flag,
            confidence=stored.confidence,
            source_page=stored.source_page,
        )
        analysis = analyze_result(parsed)
        stored.status = analysis.status
        stored.critical_flag = analysis.critical_flag
        stored.unit_converted = analysis.unit_converted
        stored.notes = analysis.notes

    db.commit()
    report = _load_report(db, current_user.id, report_id)
    results = [_result_out(result) for result in report.results]
    return AnalyzeResponse(
        report_id=report.id,
        abnormal_count=sum(1 for r in report.results if r.status in ABNORMAL_STATUSES),
        results=results,
    )


@router.post("/{report_id}/explain", response_model=ExplainResponse)
def explain_report(
    report_id: int,
    language: str = Query(default="en"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExplainResponse:
    language = language.lower()
    if language not in LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language. Use one of: {', '.join(LANGUAGES)}.",
        )

    report = _load_report(db, current_user.id, report_id)
    if not report.results:
        raise HTTPException(status_code=400, detail="This report has no extracted results.")

    engine = ExplanationEngine(get_provider())
    items: list[ExplanationItem] = []

    for result in report.results[:MAX_EXPLANATIONS_PER_REQUEST]:
        context = _result_context(result)
        generated = engine.generate(context, language)

        existing: Optional[Explanation] = db.scalar(
            select(Explanation).where(
                Explanation.result_id == result.id,
                Explanation.language == language,
            )
        )
        if existing is None:
            existing = Explanation(
                result_id=result.id,
                language=language,
                text=generated.text,
                model=generated.model,
                source=generated.source,
            )
            db.add(existing)
        else:
            existing.text = generated.text
            existing.model = generated.model
            existing.source = generated.source

        items.append(
            ExplanationItem(
                result_id=result.id,
                test_name=result.test_name,
                text=generated.text,
                model=generated.model,
                source=generated.source,
            )
        )

    db.commit()

    used_llm = any(item.source != "template" for item in items)
    provider = engine.provider.label() if used_llm and engine.provider else "template"

    return ExplainResponse(
        report_id=report.id,
        language=language,
        provider=provider,
        explanations=items,
        disclaimer=EXPLANATION_DISCLAIMER,
    )


@router.post("/{report_id}/chat", response_model=ChatResponse)
def chat_with_report(
    report_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    language = payload.language
    if language not in LANGUAGES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported language. Use one of: {', '.join(LANGUAGES)}.",
        )

    report = _load_report(db, current_user.id, report_id)
    if report.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only completed reports can be discussed.",
        )
    if not report.results:
        raise HTTPException(status_code=400, detail="This report has no extracted results.")

    history = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.report_id == report.id)
        .order_by(ChatMessage.id)
    ).all()

    db.add(
        ChatMessage(
            report_id=report.id,
            user_id=current_user.id,
            role="user",
            content=payload.message,
            language=language,
            model="user",
            source="user",
        )
    )
    db.commit()

    engine = ChatEngine(get_provider())
    answer = engine.answer(
        payload.message,
        [_result_context(result) for result in report.results],
        language,
        history=[(message.role, message.content) for message in history],
    )

    assistant = ChatMessage(
        report_id=report.id,
        user_id=current_user.id,
        role="assistant",
        content=answer.text,
        language=language,
        model=answer.model,
        source=answer.source,
        cited_result_ids=answer.cited_result_ids,
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)

    provider_label = (
        engine.provider.label()
        if answer.source != "template" and engine.provider is not None
        else "template"
    )
    return ChatResponse(
        report_id=report.id,
        language=language,
        provider=provider_label,
        reply=ChatMessageOut.model_validate(assistant),
        disclaimer=CHAT_DISCLAIMER,
    )


@router.get("/{report_id}/chat", response_model=ChatHistoryResponse)
def get_chat_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    report = _load_report(db, current_user.id, report_id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.report_id == report.id, ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.id)
    ).all()
    return ChatHistoryResponse(
        report_id=report.id,
        messages=[ChatMessageOut.model_validate(message) for message in messages[-200:]],
        disclaimer=CHAT_DISCLAIMER,
    )


@router.delete("/{report_id}/chat", status_code=status.HTTP_204_NO_CONTENT)
def clear_chat_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    report = _load_report(db, current_user.id, report_id)
    db.execute(
        delete(ChatMessage).where(
            ChatMessage.report_id == report.id,
            ChatMessage.user_id == current_user.id,
        )
    )
    db.commit()


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    report = _load_report(db, current_user.id, report_id)
    stored_path = Path(report.stored_path)
    db.delete(report)
    db.commit()
    _delete_file(stored_path)
