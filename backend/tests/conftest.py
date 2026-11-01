"""Test configuration: isolated database, uploads and disabled AI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="mediexplain-test-"))

os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_ROOT / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TEST_ROOT / "uploads")
os.environ["PROCESSED_DIR"] = str(_TEST_ROOT / "processed")
os.environ["AI_PROVIDER"] = "none"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "test"

TEST_ROOT = _TEST_ROOT


@pytest.fixture(scope="session")
def client():
    """TestClient used as a context manager so the app lifespan runs."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
