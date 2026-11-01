"""MediExplain AI FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import init_db
from app.routes import api_router
from services import ocr_engine
from services.ai.llm_provider import get_provider

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Third-party libraries are extremely chatty at DEBUG level and drown out
# application logs (pdfminer dumps every PDF token).
for _noisy in ("pdfminer", "pdfplumber", "httpcore", "httpx", "urllib3", "asyncio"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    init_db()
    provider = get_provider()
    logging.getLogger(__name__).info(
        "MediExplain AI started | AI provider=%s | OCR=%s",
        provider.label() if provider else "template-only",
        "available" if ocr_engine.is_available() else "unavailable",
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Educational medical report analysis. Not a diagnostic system and not a "
        "substitute for professional medical advice."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
        "disclaimer": "Informational only. Not a diagnosis and not medical advice.",
    }


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    provider = get_provider()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "ai_provider": provider.label() if provider else "template",
        "ocr_available": ocr_engine.is_available(),
    }
