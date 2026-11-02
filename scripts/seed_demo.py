"""Create (or refresh) the demo account and attach the synthetic sample reports.

Usage (from the repository root):

    backend\\.venv\\Scripts\\python.exe scripts\\seed_demo.py

The script is idempotent: it reuses an existing demo user and skips samples
that have already been uploaded. Every value in the sample reports is fake.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

# Resolve the backend .env, SQLite file and upload folder relative to backend/.
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.models import Report, TestResult, User  # noqa: E402
from app.routes.reports import _to_model_value  # noqa: E402
from app.utils.files import safe_original_name, store_upload, validate_upload  # noqa: E402
from services.document_processor import process_document  # noqa: E402

DEMO_EMAIL = "demo@mediexplain.app"
DEMO_PASSWORD = "DemoPass123"
DEMO_NAME = "Demo Patient"

SAMPLE_DIR = REPO_ROOT / "samples"
SAMPLES = ("sample_cbc_report.pdf", "sample_lipid_report.pdf")


def get_or_create_demo_user(db) -> User:
    user = db.scalar(select(User).where(func.lower(User.email) == DEMO_EMAIL))
    if user is None:
        user = User(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created demo user: {DEMO_EMAIL}")
        return user

    # Keep the demo credentials predictable even if the row already existed.
    user.name = DEMO_NAME
    user.password_hash = hash_password(DEMO_PASSWORD)
    db.commit()
    db.refresh(user)
    print(f"Reused demo user: {DEMO_EMAIL}")
    return user


def seed_sample(db, user: User, sample_path: Path) -> str:
    data = sample_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()

    existing = db.scalar(
        select(Report).where(
            Report.user_id == user.id,
            Report.file_hash == digest,
        )
    )
    if existing is not None:
        return f"skipped (already attached as report #{existing.id})"

    extension, mime_type = validate_upload(sample_path.name, data)
    stored_path = store_upload(settings.upload_path, user.id, data, extension)

    report = Report(
        user_id=user.id,
        original_filename=safe_original_name(sample_path.name),
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
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        report.status = "failed"
        report.error_message = "Demo seeding failed. Check the backend logs."
        db.commit()
        stored_path.unlink(missing_ok=True)
        raise RuntimeError(f"Could not process {sample_path.name}: {exc}") from exc

    return f"attached as report #{report.id} ({len(document.results)} results)"


def main() -> int:
    init_db()
    with SessionLocal() as db:
        user = get_or_create_demo_user(db)

        for filename in SAMPLES:
            sample_path = SAMPLE_DIR / filename
            if not sample_path.exists():
                print(f"Missing sample: {sample_path}")
                return 1
            outcome = seed_sample(db, user, sample_path)
            print(f"  {filename}: {outcome}")

        report_count = db.scalar(
            select(func.count()).select_from(Report).where(Report.user_id == user.id)
        )

    print()
    print("Demo account ready")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print(f"  Reports:  {report_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
