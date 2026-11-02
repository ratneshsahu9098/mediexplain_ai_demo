"""Application configuration loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "MediExplain AI"
    environment: str = "development"
    debug: bool = True

    secret_key: str = "dev-only-secret-change-me"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite:///./mediexplain.db"

    upload_dir: str = "../data/uploads"
    processed_dir: str = "../data/processed"
    max_upload_mb: int = 15
    max_pdf_pages: int = 25
    allowed_extensions: str = ".pdf,.jpg,.jpeg,.png"

    tesseract_cmd: str = ""
    ocr_dpi: int = 300

    ai_provider: str = "ollama"  # ollama | openrouter | cloud | none
    ai_timeout_seconds: int = 120
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto"
    openrouter_site_url: str = ""
    cloud_llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    cloud_llm_api_key: str = ""
    cloud_llm_model: str = "gemini-2.0-flash"

    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            ext.strip().lower()
            for ext in self.allowed_extensions.split(",")
            if ext.strip()
        }

    @property
    def upload_path(self) -> Path:
        return self._resolve(self.upload_dir)

    @property
    def processed_path(self) -> Path:
        return self._resolve(self.processed_dir)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origins.split(",") if o.strip()]

    @staticmethod
    def _resolve(value: str) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = (BACKEND_DIR / path).resolve()
        return path

    def ensure_directories(self) -> None:
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
